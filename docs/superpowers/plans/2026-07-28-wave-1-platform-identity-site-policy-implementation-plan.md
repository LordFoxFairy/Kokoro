# Wave 1 Platform / Identity / Site / Policy Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a production-qualified PostgreSQL Platform control plane with complete Site-bound Identity, personal Workspace bootstrap, immutable Site release lifecycle, secure Admin operations, local ModelControl ownership, Data Rights participation, redeem-only Payment closure, two independent Site projects, and backup/restore/DR evidence—without changing GA runtime semantics.

**Architecture:** Root remains contract, Infra, compatibility, BOM, and pin-promotion authority. `kokoro-platform` is one deployable bounded context using a PostgreSQL modular monolith: owner modules collaborate through application ports and a single opaque Unit of Work, while true remote systems use generated Connect/HTTP contracts plus durable intent/reconciliation. Each public Site is an independent Web repository/artifact/deployment that consumes signed app-kit and generated clients. W2A exclusively owns Redeem/Fulfillment/Credit facts; W3 owns Session admission and Chat Web runtime. GA remains an opaque namespace consumer and its existing control wire is frozen.

**Tech Stack:** TypeScript 5.9, Node.js 24, pnpm 11, PostgreSQL 18, Prisma 7, Zod 4 for new runtime boundaries, ConnectRPC/Protobuf, OpenAPI 3.1, Next.js/Auth.js, Vitest, Node test runner, Playwright, Buf, Docker Compose (single shared default Infra lifecycle only). Legacy Zod 3 consumers remain supported only through Root-generated cross-version-compatible mirrors until their owning cutover task removes them.

---

## Execution rules and dependency graph

- Root, `kokoro-platform`, and `kokoro-web` are separate repositories. Every task commits in its owning repository; only Task 20 promotes child pins in Root.
- The single-writer DAG is fixed: Root `Task 0 → 1 → 2A`, then delayed `Task 2B` after PostgreSQL consumers are ready;
  Platform `Task 3 → 4 → … → 14 → 14B → 15 → 16 → 17 → 19`; Web package scaffolding in `Task 18` may run
  after Task 1's generated-contract handoff, but its authenticated runtime journey requires Platform Task 14B; Task 20 joins the clean child commits. Exactly one worker owns each repository
  worktree/index/lockfile at a time. Tasks within `kokoro-platform` are serial; no Site/Identity/Admin/ModelControl parallel writes.
- Tasks 1–19 MUST NOT start a private Docker/Compose stack. Unit and contract tests run without containers; PostgreSQL component tests reuse the single Root-managed default Infra instance through a leased database/role.
- The Root integrator may perform only Task 2A's additive PostgreSQL candidate lifecycle, Task 2B's bounded default-Infra
  MySQL→PostgreSQL activation/lease, and Task 20's final
  reconciliation. No other worker may start a stack. Both operations preserve Redis/Mongo/MinIO and never prune/delete volumes,
  images, or developer data.
- No task edits `kokoro-agent`. GA verification is read-only: golden-byte, forbidden-field, and compatibility assertions only.
- `chat.execution.prepare`, Redeem routes, and Credit admission remain absent until both their owner Waves are independently qualified. A placeholder, compatibility route, or declared-but-unimplemented descriptor is a failure.
- Cross-repository Web Task 18 may overlap the serial Platform lane only after Task 1 handoff. Task 19 follows all Platform consumer
  cutovers; Task 20 is serial integration. Every task stages only declared paths with `git add --`; `git add -A` is forbidden.

### Task 0: Install and pass the executable approval/dependency baseline gate

**Repository:** Root

**Files:**

- Create: `scripts/wave1/preflight.mjs`
- Create: `scripts/wave1/preflight.test.mjs`
- Runtime-only, never commit: `.git/kokoro-wave1/baseline.json`

- [ ] Write failing fixture tests for unapproved/unauthorized Wave 1 spec, missing or mismatched ADR-012 digest/adoption and ADR-005
  supersession, parent-spec mismatch, absent evidence/pin/contract digest, dirty Root/child state, or unexpected child SHA.
- [ ] Add GA baseline fixtures requiring exact `kokoro-agent` SHA, full porcelain status including untracked files, and SHA-256 of
  `contract/spec/control.yaml` plus `kokoro-agent/src/kokoro_agent/contract/control.py`.
- [ ] Run `node --test scripts/wave1/preflight.test.mjs`; confirm RED because the gate is missing.
- [ ] Implement a read-only, fail-closed checker that atomically writes the baseline only after all approval, ADR, evidence,
  generated-contract, pin and clean-worktree requirements pass.
- [ ] Run `node --test scripts/wave1/preflight.test.mjs`, then separately run
  `node scripts/wave1/preflight.mjs --write-baseline .git/kokoro-wave1/baseline.json`. Any failure stops before Task 1; this plan
  cannot change approved spec/ADR state or fabricate evidence.
- [ ] Commit only the gate: `git add -- scripts/wave1/preflight.mjs scripts/wave1/preflight.test.mjs && git commit -m "build(wave1): add approval and isolation preflight"`.

## Chunk 1 — Root authority and Platform kernel

### Task 1: Freeze Wave 1 public and privileged contracts

**Repository:** Root

**Files:**

- Create: `contract/openapi/platform-public-v1.yaml`
- Create: `contract/proto/kokoro/platform/site/v1/site_lifecycle.proto`
- Create: `contract/proto/kokoro/platform/identity/v1/admin_identity.proto`
- Create: `contract/proto/kokoro/platform/admin/v2/admin_shared.proto`
- Create: `contract/proto/kokoro/platform/admin/v2/admin_query.proto`
- Create: `contract/proto/kokoro/platform/admin/v2/admin_command.proto`
- Create: `contract/proto/kokoro/common/v2/command_envelope.proto`
- Modify: `contract/buf.yaml`
- Modify: `contract/generate.mjs`
- Modify: `contract/package.json`
- Modify: `contract/pnpm-lock.yaml`
- Modify: `contract/registry/boundaries.schema.json`
- Modify: `contract/registry/boundaries.yaml`
- Modify: `contract/tests/test_buf_contract.py`
- Modify: `contract/tests/test_generate.py`
- Create: `scripts/contract/check-wave1-surface.mjs`
- Create: `scripts/contract/check-wave1-surface.test.mjs`
- Create: `scripts/contract/openapi-reader.mjs`
- Create: `scripts/contract/read-openapi.py`
- Modify: `scripts/contract/check-boundary-registry.mjs`
- Modify: `scripts/contract/check-boundary-registry.test.mjs`
- Modify: `scripts/contract/INDEX.md`
- Modify: `scripts/repository/check-generated-contracts.test.mjs`
- Modify: `.github/workflows/contract.yml`

- [ ] Write failing contract tests for Site-bound registration/login/session management, per-operation typed public results,
  one-time no-store payloads, caller-generated command IDs, server-keyed request digests, caller-held recovery capabilities,
  loss-safe receipt/supersede state machines, Site lifecycle/release commands, pre-login versus authenticated Admin contexts,
  Platform-owned PKCE redemption, code-free Admin delivery recovery, fixed signed-then-encrypted JOSE delivery, typed Admin
  scope/axes/approval, stable error codes, request IDs, idempotency keys, strict OpenAPI YAML parsing, and sibling-free generated
  consumer artifacts. Assert that no Payment purchase route and no `chat.execution.prepare` descriptor exists.
- [ ] Freeze typed provisioning/activation receipt reads so zero-byte first responses and provider outcome-unknown states resume
  the same durable intent/attempt through explicit phases; `same_identity` must never masquerade as final deployment evidence.
- [ ] Run `uv run --locked python -m pytest contract/tests/test_buf_contract.py contract/tests/test_generate.py -q`; record its
  expected RED independently. Then run `node --test scripts/contract/check-wave1-surface.test.mjs`; record its expected RED
  independently. Do not join expected-red suites with `&&`, which would short-circuit the second test.
- [ ] Add additive versioned contracts and exact boundary registry ownership. Keep the byte-frozen V1 envelope for legacy
  boundaries and use V2 canonical scope/Site/actor/resource binding plus typed digest helpers for new privileged effects. Registry
  receipt refs must exist in the real RPC response; `reconcile_receipt` command/state receipts must name a reachable non-effect
  recovery operation. Keep public browser HTTP separate from privileged ConnectRPC; do not expose raw database identifiers or
  internal policy records. Never use an unresolved generic `resultRef` for credentials, device/session lists, personal context,
  enrollment secret, or recovery codes.
- [ ] Generate deterministic mirrors with `pnpm --dir contract buf:lint && pnpm --dir contract buf:generate`; ensure a second generation produces no diff.
- [ ] Run the targeted tests plus `node scripts/contract/check-boundary-coverage.mjs`; confirm all new provider/consumer edges match the exact boundary, not merely the repository pair.
- [ ] Commit only declared Task 1 paths, including the V2 envelope, strict OpenAPI dependency pins/CI, registry schema/checker,
  generator mirrors and contract index; stage them explicitly with `git add -- <Task-1-paths>` and never use `git add -A`.

### Task 2A: Add the PostgreSQL transition foundation without changing the default MySQL contract

**Repository:** Root

**Files:**

- Modify: `docker-compose.infra.yml`
- Modify: `config/repository/infrastructure-policy.yaml`
- Modify: `deploy/.env.example`
- Modify: `scripts/infra/manager.mjs`
- Modify: `scripts/infra/manager.test.mjs`
- Modify: `scripts/infra/scope.mjs`
- Modify: `scripts/infra/scope.test.mjs`
- Modify: `scripts/infra/inventory.mjs`
- Modify: `scripts/infra/inventory.test.mjs`
- Modify: `scripts/infra/INDEX.md`

- [ ] Write failing tests for a digest-pinned PostgreSQL 18 candidate profile, separate Platform/Session databases and
  API/worker/migrator/test roles, safe leased cleanup, credential/persistent-volume auth-generation drift, sanitized deterministic
  inventory record/check receipts, and rejection of destructive Docker operations.
- [ ] Add a regression test proving `platform` and `full` still select MySQL and that generic `ensure` never force-recreates a
  mismatched stateful stack. A scope mismatch must fail with an explicit-activation error.
- [ ] Run `node --test scripts/infra/manager.test.mjs scripts/infra/scope.test.mjs scripts/infra/inventory.test.mjs`; confirm RED on
  the missing additive profile, lease, drift gates, and inventory receipt behavior.
- [ ] Add `postgres-transition` to the one Root-owned Compose project and policy. It is additive and
  `activationAuthorized=false`; do not edit the canonical `platform`/`full` MySQL membership in 2A.
- [ ] Add explicit PostgreSQL-only leases for Platform/Session databases and bounded API/worker/migrator/test roles while retaining
  current MySQL compatibility leases. PostgreSQL-only leases must not reserve Redis capacity.
- [ ] Implement metadata-only inventory `--record <path>` / `--check <path>`, non-secret data/auth generation markers, and hard
  denials for prune/remove/down-with-volumes/orphan-removal. Never inspect container env or mount host paths.
- [ ] Re-run all non-Docker Infra tests. Task 2A must not inspect, start, stop, or reconcile Docker and must not produce an activation
  receipt; it only makes the candidate safe to start later through the canonical manager.
- [ ] Commit in Root: `git add -- docker-compose.infra.yml config/repository/infrastructure-policy.yaml deploy/.env.example scripts/infra/manager.mjs scripts/infra/manager.test.mjs scripts/infra/scope.mjs scripts/infra/scope.test.mjs scripts/infra/inventory.mjs scripts/infra/inventory.test.mjs scripts/infra/INDEX.md docs/superpowers/plans/2026-07-28-wave-1-platform-identity-site-policy-implementation-plan.md && git commit -m "feat(infra): add guarded postgres transition foundation"`.

### Task 2B: Activate PostgreSQL only after consumers and rollback evidence are ready

**Repository:** Root

**Depends on:** Task 2A plus reviewed PostgreSQL support in every Platform/Session consumer selected for activation.

- [ ] Add failing activation tests first. Require an immutable baseline inventory digest, exact candidate/consumer SHAs, no active
  test leases, no competing Kokoro Compose authority, matching persistent-auth generations, healthy PostgreSQL, and an explicit
  one-time activation intent. Missing or stale evidence fails closed.
- [ ] Record the baseline with `node scripts/infra/inventory.mjs --record <baseline-path>`. Compare exact service/image/profile/port/
  volume/health/data-marker identities and prove Redis, Mongo, MinIO, and LiteLLM are the preserved set.
- [ ] Change only the canonical database selection from MySQL to PostgreSQL. Do not force-recreate preserved services, delete either
  database volume, prune images/volumes, or use a second Compose project. Stop/archive the MySQL service only after traffic readiness.
- [ ] Acquire explicit PostgreSQL test leases, run the ready consumers' component/compatibility suites, and persist a sanitized
  activation receipt binding before/after inventory digests, consumer SHAs, checks, and rollback pointer.
- [ ] Rehearse rollback by stopping only the candidate database and restoring the canonical MySQL pointer/service; verify preserved
  service identities remain byte-for-byte equal. A rollback must not recreate Redis, Mongo, MinIO, or LiteLLM.
- [ ] Run `node --test scripts/infra/*.test.mjs`, `node scripts/infra/inventory.mjs --check <baseline-or-approved-transition-path> --expect-digest <externally-pinned-sha256>`,
  rendered Compose validation, consumer compatibility, and receipt validation before committing the bounded activation.

### Task 3: Establish the Platform PostgreSQL schema, clients, migrator, and deployable roles

**Repository:** `kokoro-platform`

**Files:**

- Create: `prisma/schema.prisma`
- Create: `prisma.config.ts`
- Create: `prisma/migrations/0001_platform_foundation/migration.sql`
- Create: `src/infrastructure/postgres/client.ts`
- Create: `src/infrastructure/postgres/migrator.ts`
- Create: `src/process/api.ts`
- Create: `src/process/worker.ts`
- Modify: `package.json`
- Modify: `pnpm-lock.yaml`
- Create: `test/component/postgres-foundation.test.ts`
- Create: `test/architecture/deployable-roles.test.ts`

- [ ] Write failing tests for one Platform database authority, separate runtime/migrator credentials, explicit statement/lock/idle transaction timeouts, transaction isolation selection, migration advisory lock, and independently startable API/Worker/migrator roles.
- [ ] Run `pnpm vitest run test/component/postgres-foundation.test.ts test/architecture/deployable-roles.test.ts`; confirm RED because the root Platform schema and roles do not exist.
- [ ] Add pinned Prisma 7/PostgreSQL dependencies, safe client construction, one-shot migrator, process health/readiness behavior, and shutdown draining. Do not add self-RPC between local modules.
- [ ] Run `pnpm db:generate && pnpm typecheck && pnpm vitest run test/architecture/deployable-roles.test.ts`; then run the component test against the pre-existing leased default PostgreSQL database.
- [ ] Commit in Platform: `git add -- prisma/schema.prisma prisma.config.ts prisma/migrations/0001_platform_foundation/migration.sql src/infrastructure/postgres/client.ts src/infrastructure/postgres/migrator.ts src/process/api.ts src/process/worker.ts package.json pnpm-lock.yaml test/component/postgres-foundation.test.ts test/architecture/deployable-roles.test.ts && git commit -m "feat(platform): establish postgres runtime foundation"`.

### Task 4: Implement the opaque Unit of Work, owner ports, outbox/inbox, and import gates

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/shared/unit-of-work/platform-transaction.ts`
- Create: `src/shared/unit-of-work/unit-of-work.ts`
- Create: `src/shared/outbox-inbox/outbox.ts`
- Create: `src/shared/outbox-inbox/inbox.ts`
- Create: `src/shared/outbox-inbox/receipt.ts`
- Create: `src/shared/INDEX.md`
- Create: `test/unit/unit-of-work.test.ts`
- Create: `test/component/outbox-inbox.test.ts`
- Create: `test/architecture/module-imports.test.ts`
- Modify: `eslint.config.mjs`

- [ ] Write failing tests proving atomic domain writes/outbox/command receipts, inbox deduplication by provider+operation+idempotency key, rollback on every local failure, and retry-safe observed outcome recording.
- [ ] Add failing architecture tests that reject raw Prisma handles outside `infrastructure/postgres`, sibling module `infrastructure` imports, deep imports, and network calls from a transaction callback.
- [ ] Run `pnpm vitest run test/unit/unit-of-work.test.ts test/component/outbox-inbox.test.ts test/architecture/module-imports.test.ts`; confirm RED.
- [ ] Implement `PlatformTransaction` as an opaque capability that exposes owner-scoped repositories only. Add outbox/inbox/receipt adapters and ESLint boundaries; local workflows receive application ports, never Prisma.
- [ ] Re-run targeted tests, `pnpm lint`, and `pnpm typecheck`; inspect that no local module URL/env/service-discovery config was introduced.
- [ ] Commit in Platform: `git add -- src/shared/unit-of-work/platform-transaction.ts src/shared/unit-of-work/unit-of-work.ts src/shared/outbox-inbox/outbox.ts src/shared/outbox-inbox/inbox.ts src/shared/outbox-inbox/receipt.ts src/shared/INDEX.md test/unit/unit-of-work.test.ts test/component/outbox-inbox.test.ts test/architecture/module-imports.test.ts eslint.config.mjs && git commit -m "feat(platform): add transactional module kernel"`.

### Task 5: Enforce RequestSecurityContext, operation policy, and Risk snapshots

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/shared/security-context/request-security-context.ts`
- Create: `src/modules/policy/domain/operation-policy.ts`
- Create: `src/modules/policy/application/contracts/risk-assessor.ts`
- Create: `src/modules/policy/application/services/authorize-effect.ts`
- Create: `src/modules/policy/infrastructure/postgres/policy-repository.ts`
- Create: `src/modules/policy/INDEX.md`
- Create: `test/unit/operation-policy.test.ts`
- Create: `test/component/effect-point-authorization.test.ts`

- [ ] Write failing tables for Site, user/operator, audience, environment, region, device, workspace, capability, session epoch, policy epoch, suspension state, risk result, and breakglass axes. Missing or mismatched axes must deny.
- [ ] Write failing race tests: obtain remote Risk snapshot before opening the transaction, then revalidate the local user/Site/policy epochs at the effect point; suspension/revoke between assessment and write must deny without side effects.
- [ ] Run `pnpm vitest run test/unit/operation-policy.test.ts test/component/effect-point-authorization.test.ts`; confirm RED.
- [ ] Implement typed immutable security context and operation-policy evaluation. Persist only signed/identified Risk evidence; prohibit Risk network access inside Unit of Work.
- [ ] Re-run targeted tests, import gates, lint, and typecheck.
- [ ] Commit in Platform: `git add -- src/shared/security-context/request-security-context.ts src/modules/policy/domain/operation-policy.ts src/modules/policy/application/contracts/risk-assessor.ts src/modules/policy/application/services/authorize-effect.ts src/modules/policy/infrastructure/postgres/policy-repository.ts src/modules/policy/INDEX.md test/unit/operation-policy.test.ts test/component/effect-point-authorization.test.ts && git commit -m "feat(platform): enforce effect point policy"`.

## Chunk 2 — ModelControl and complete Site lifecycle

### Task 6: Migrate ModelControl to its canonical local owner

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/modules/model-control/domain/model-catalog.ts`
- Create: `src/modules/model-control/application/contracts/model-control-ports.ts`
- Create: `src/modules/model-control/application/services/import-model-control.ts`
- Create: `src/modules/model-control/application/services/resolve-model-policy.ts`
- Create: `src/modules/model-control/infrastructure/postgres/model-control-repository.ts`
- Create: `src/modules/model-control/INDEX.md`
- Create: `scripts/model-control/export-legacy.mts`
- Create: `scripts/model-control/import-canonical.mts`
- Create: `test/component/model-control-import.test.ts`
- Create: `test/architecture/model-control-consumers.test.ts`

- [ ] Write failing tests for immutable source export digest, transactional import, projection parity, global base inventory, product-specific lists (Chat/Music/Image/Video), default main model, fallback chain, Site assignments, capability constraints, disabled-provider behavior, and per-Site authorization.
- [ ] Add a failing scan requiring all Platform consumers to call the local owner port and forbidding new consumers of the legacy `kokoro-model` process. The remote Model Gateway remains a provider execution boundary.
- [ ] Run `pnpm vitest run test/component/model-control-import.test.ts test/architecture/model-control-consumers.test.ts`; confirm RED.
- [ ] Implement the target module and repeatable import with source/import digests; migrate consumers before removal and make fallback selection deterministic/auditable.
- [ ] Run parity twice against a fresh leased database and verify identical digest and row counts; run lint/typecheck.
- [ ] Commit in Platform: `git add -- src/modules/model-control/domain/model-catalog.ts src/modules/model-control/application/contracts/model-control-ports.ts src/modules/model-control/application/services/import-model-control.ts src/modules/model-control/application/services/resolve-model-policy.ts src/modules/model-control/infrastructure/postgres/model-control-repository.ts src/modules/model-control/INDEX.md scripts/model-control/export-legacy.mts scripts/model-control/import-canonical.mts test/component/model-control-import.test.ts test/architecture/model-control-consumers.test.ts && git commit -m "feat(platform): make model control canonical"`.

### Task 7: Build Site aggregate, binding, immutable releases, and active-pointer CAS

**Repository:** `kokoro-platform`

**Files:**

- Modify: `prisma/schema.prisma`
- Create: `prisma/migrations/0002_site_release_binding/migration.sql`
- Create: `src/modules/site/domain/site.ts`
- Create: `src/modules/site/domain/site-release.ts`
- Create: `src/modules/site/domain/site-binding.ts`
- Create: `src/modules/site/application/contracts/site-ports.ts`
- Create: `src/modules/site/infrastructure/postgres/site-repository.ts`
- Create: `src/modules/site/INDEX.md`
- Create: `test/component/site-aggregate.test.ts`

- [ ] Write failing constraints for Site key/state/epoch, globally unambiguous verified domain binding, immutable release/profile/brand/SEO/artifact/contract digests, release compatibility floor, and one CAS active pointer.
- [ ] Add concurrency failures for duplicate keys/domains, stale activation, release mutation, cross-Site lookup, and host-header fallback. Site resolution must use an explicit trusted binding.
- [ ] Run `pnpm vitest run test/component/site-aggregate.test.ts`; confirm RED.
- [ ] Add schema, owner repository, and domain transitions in one UoW. Store provenance/digests, not mutable Web build configuration.
- [ ] Re-run against PostgreSQL, then lint/typecheck/import gates.
- [ ] Commit in Platform: `git add -- prisma/schema.prisma prisma/migrations/0002_site_release_binding/migration.sql src/modules/site/domain/site.ts src/modules/site/domain/site-release.ts src/modules/site/domain/site-binding.ts src/modules/site/application/contracts/site-ports.ts src/modules/site/infrastructure/postgres/site-repository.ts src/modules/site/INDEX.md test/component/site-aggregate.test.ts && git commit -m "feat(platform): add immutable site releases"`.

### Task 8: Implement Site request, provisioning intents, and reconciliation

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/workflows/site-lifecycle/request-site.ts`
- Create: `src/workflows/site-lifecycle/provision-site.ts`
- Create: `src/workflows/site-lifecycle/reconcile-provisioning.ts`
- Create: `src/modules/site/application/services/site-provisioning.ts`
- Create: `src/interfaces/connect/site-lifecycle.ts`
- Create: `test/component/site-provisioning.test.ts`
- Create: `test/contract/site-lifecycle-connect.test.ts`

- [ ] Write failing state-machine tests for requested→provisioning→ready/failed, idempotent commands, durable external deployment intents, timeout/unknown outcome, observation, bounded retry, poison receipt, and operator recovery.
- [ ] Prove no repository transaction performs DNS, build, Git, secret-manager, or deployment network calls; commit local intent first and reconcile external observations later.
- [ ] Run `pnpm vitest run test/component/site-provisioning.test.ts test/contract/site-lifecycle-connect.test.ts`; confirm RED.
- [ ] Implement workflow/application services and generated Connect adapter. Authenticate workload identity and bind every command to exact Site/environment/idempotency context.
- [ ] Re-run targeted tests and the module import/network-in-transaction gates.
- [ ] Commit in Platform: `git add -- src/workflows/site-lifecycle/request-site.ts src/workflows/site-lifecycle/provision-site.ts src/workflows/site-lifecycle/reconcile-provisioning.ts src/modules/site/application/services/site-provisioning.ts src/interfaces/connect/site-lifecycle.ts test/component/site-provisioning.test.ts test/contract/site-lifecycle-connect.test.ts && git commit -m "feat(platform): orchestrate site provisioning"`.

### Task 9: Qualify activation, drain, rollback, and unknown release outcomes

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/workflows/site-lifecycle/activate-release.ts`
- Create: `src/workflows/site-lifecycle/drain-release.ts`
- Create: `src/workflows/site-lifecycle/rollback-release.ts`
- Create: `src/modules/site/application/services/release-lifecycle.ts`
- Create: `test/component/site-release-lifecycle.test.ts`
- Create: `test/contract/site-release-receipts.test.ts`

- [ ] Write failing tests for signed artifact/manifest verification, compatibility-floor rejection, canary observation, CAS activate, drain deadline, rollback to prior immutable release, stale receipt, provider timeout, and reconcile-before-retry.
- [ ] Include simultaneous activate/rollback and two-Site interleaving tests; an observation for Site A must never advance Site B.
- [ ] Run `pnpm vitest run test/component/site-release-lifecycle.test.ts test/contract/site-release-receipts.test.ts`; confirm RED.
- [ ] Implement release workflows using durable attempts and observations; never infer provider success from a timeout and never mutate an existing release.
- [ ] Re-run targeted tests plus Postgres concurrency tests.
- [ ] Commit in Platform: `git add -- src/workflows/site-lifecycle/activate-release.ts src/workflows/site-lifecycle/drain-release.ts src/workflows/site-lifecycle/rollback-release.ts src/modules/site/application/services/release-lifecycle.ts test/component/site-release-lifecycle.test.ts test/contract/site-release-receipts.test.ts && git commit -m "feat(platform): qualify site release lifecycle"`.

### Task 10: Complete suspend, resume, decommission, and domain reuse semantics

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/workflows/site-lifecycle/suspend-site.ts`
- Create: `src/workflows/site-lifecycle/resume-site.ts`
- Create: `src/workflows/site-lifecycle/decommission-site.ts`
- Create: `src/modules/site/domain/site-disposition.ts`
- Create: `test/component/site-disposition.test.ts`
- Create: `test/contract/site-participant-receipts.test.ts`

- [ ] Write failing tests for immediate epoch invalidation, product-side-effect denial, narrowly typed Support/DataRights/mandatory-inbound access, participant plan/execute/verify receipts, LegalHold denial, partial-failure resume, tombstone retention, and domain quarantine/reuse approval.
- [ ] Prove suspend/resume races cannot reactivate stale sessions or releases; prove decommission never deletes before all required participant verification receipts exist.
- [ ] Run `pnpm vitest run test/component/site-disposition.test.ts test/contract/site-participant-receipts.test.ts`; confirm RED.
- [ ] Implement state transitions and durable participant orchestration. Domain reuse requires explicit verified disposition and new binding generation.
- [ ] Re-run targeted tests, lint, typecheck, and policy effect-point tests.
- [ ] Commit in Platform: `git add -- src/workflows/site-lifecycle/suspend-site.ts src/workflows/site-lifecycle/resume-site.ts src/workflows/site-lifecycle/decommission-site.ts src/modules/site/domain/site-disposition.ts test/component/site-disposition.test.ts test/contract/site-participant-receipts.test.ts && git commit -m "feat(platform): close site disposition lifecycle"`.

## Chunk 3 — Complete Identity and personal Workspace bootstrap

### Task 11: Implement Site-bound registration, verification, and explicit login separation

**Repository:** `kokoro-platform`

**Files:**

- Modify: `prisma/schema.prisma`
- Create: `prisma/migrations/0003_identity_registration/migration.sql`
- Create: `src/modules/identity/domain/pending-registration.ts`
- Create: `src/modules/identity/domain/user-account.ts`
- Create: `src/modules/identity/application/services/begin-registration.ts`
- Create: `src/modules/identity/application/services/verify-registration.ts`
- Create: `src/modules/identity/infrastructure/postgres/identity-repository.ts`
- Create: `src/interfaces/http/identity-registration.ts`
- Create: `test/component/identity-registration.test.ts`

- [ ] Write failing tests for normalized Site-bound email uniqueness, enumeration-safe response, rate-limit evidence, single-use hashed token, expiry, resend rotation, replay rejection, concurrent verify, and same email independently registering on two Sites.
- [ ] Assert verification activates identity/bootstrap atomically but never creates an authenticated browser session; login is a separate explicit ceremony.
- [ ] Run `pnpm vitest run test/component/identity-registration.test.ts`; confirm RED.
- [ ] Implement pending-registration and activation in the Platform UoW with notification outbox and effect-point Site/policy checks.
- [ ] Re-run targeted tests against PostgreSQL and run the OpenAPI contract test.
- [ ] Commit in Platform: `git add -- prisma/schema.prisma prisma/migrations/0003_identity_registration/migration.sql src/modules/identity/domain/pending-registration.ts src/modules/identity/domain/user-account.ts src/modules/identity/application/services/begin-registration.ts src/modules/identity/application/services/verify-registration.ts src/modules/identity/infrastructure/postgres/identity-repository.ts src/interfaces/http/identity-registration.ts test/component/identity-registration.test.ts && git commit -m "feat(platform): add site bound registration"`.

### Task 12: Implement password login, TOTP, recovery codes, and session issuance

**Repository:** `kokoro-platform`

**Files:**

- Modify: `package.json`
- Modify: `pnpm-lock.yaml`

- Create: `src/modules/identity/domain/authenticator.ts`
- Create: `src/modules/identity/domain/user-session.ts`
- Create: `src/modules/identity/application/services/password-login.ts`
- Create: `src/modules/identity/application/services/totp-lifecycle.ts`
- Create: `src/modules/identity/application/services/recovery-code-lifecycle.ts`
- Create: `src/modules/identity/infrastructure/postgres/session-repository.ts`
- Create: `test/security/password-login.test.ts`
- Create: `test/security/mfa-lifecycle.test.ts`

- [ ] Write failing tests for Argon2id policy/rehash, constant-shape errors, rate limits, password+TOTP challenge binding, enrollment confirmation, replay window, hashed one-time recovery codes, rotation, disable re-auth, fixation prevention, signed opaque cookie/token claims, and session epoch.
- [ ] Add tests for disabled/suspended/unverified users, wrong Site, stale challenge, concurrent recovery-code use, clock skew, and key rotation. No custom cryptography is allowed.
- [ ] Run `pnpm vitest run test/security/password-login.test.ts test/security/mfa-lifecycle.test.ts`; confirm RED.
- [ ] Implement with reviewed libraries pinned in `package.json` (`argon2`, `otplib`, `jose`) and Platform-owned key/config ports. Store only hashes and necessary audit metadata.
- [ ] Re-run security tests, dependency audit, lint, and typecheck.
- [ ] Commit in Platform: `git add -- package.json pnpm-lock.yaml src/modules/identity/domain/authenticator.ts src/modules/identity/domain/user-session.ts src/modules/identity/application/services/password-login.ts src/modules/identity/application/services/totp-lifecycle.ts src/modules/identity/application/services/recovery-code-lifecycle.ts src/modules/identity/infrastructure/postgres/session-repository.ts test/security/password-login.test.ts test/security/mfa-lifecycle.test.ts && git commit -m "feat(platform): complete password and mfa login"`.

### Task 13: Complete credential recovery, email change, refresh rotation, and revocation

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/modules/identity/application/services/password-reset.ts`
- Create: `src/modules/identity/application/services/password-change.ts`
- Create: `src/modules/identity/application/services/account-recovery.ts`
- Create: `src/modules/identity/application/services/email-change.ts`
- Create: `src/modules/identity/application/services/session-lifecycle.ts`
- Create: `src/interfaces/http/identity-session.ts`
- Create: `test/security/identity-recovery.test.ts`
- Create: `test/security/session-lifecycle.test.ts`

- [ ] Write failing tests for reset request/consume, current-password change, full lost-factor recovery, dual confirmation for email change, re-auth freshness, refresh-token family rotation/reuse detection, device/session list, single/all revoke, user disable, and password/MFA/email epoch invalidation.
- [ ] Cover enumeration, token substitution, two-Site token confusion, parallel refresh, reset-versus-login race, lost email, lost MFA, LegalHold effects, and audit/notification outbox behavior.
- [ ] Run `pnpm vitest run test/security/identity-recovery.test.ts test/security/session-lifecycle.test.ts`; confirm RED.
- [ ] Implement all state transitions through the identity owner port and one UoW; evaluate Site/user/session epochs again at issue/refresh/revoke effect points.
- [ ] Re-run targeted security and OpenAPI contract tests, lint, and typecheck.
- [ ] Commit in Platform: `git add -- src/modules/identity/application/services/password-reset.ts src/modules/identity/application/services/password-change.ts src/modules/identity/application/services/account-recovery.ts src/modules/identity/application/services/email-change.ts src/modules/identity/application/services/session-lifecycle.ts src/interfaces/http/identity-session.ts test/security/identity-recovery.test.ts test/security/session-lifecycle.test.ts && git commit -m "feat(platform): close identity recovery and sessions"`.

### Task 14: Atomically bootstrap the personal Workspace and billing shell

**Repository:** `kokoro-platform`

**Files:**

- Modify: `prisma/schema.prisma`
- Create: `prisma/migrations/0004_personal_workspace/migration.sql`
- Create: `src/modules/workspace/domain/personal-workspace.ts`
- Create: `src/modules/workspace/application/services/bootstrap-personal-workspace.ts`
- Create: `src/modules/workspace/infrastructure/postgres/workspace-repository.ts`
- Create: `src/modules/commerce/domain/personal-billing-account.ts`
- Create: `src/workflows/registration/activate-registration.ts`
- Create: `test/component/personal-bootstrap.test.ts`

- [ ] Write failing tests requiring user, personal Workspace, owner Membership, personal BillingAccount shell, default Project, ExecutionSpace, and namespace-allocation intent to commit exactly once in the registration activation UoW.
- [ ] Assert rollback leaves none of those records; retry converges; same email on another Site receives distinct IDs/namespaces. Assert no Redeem/Fulfillment/Grant/Journal/Hold fact or Credit balance is created in W1.
- [ ] Run `pnpm vitest run test/component/personal-bootstrap.test.ts`; confirm RED.
- [ ] Implement owner modules and activation workflow; external namespace allocation is a durable intent reconciled after commit, never a GA call in transaction.
- [ ] Re-run targeted tests and architecture scans for W2A ownership violations.
- [ ] Commit in Platform: `git add -- prisma/schema.prisma prisma/migrations/0004_personal_workspace/migration.sql src/modules/workspace/domain/personal-workspace.ts src/modules/workspace/application/services/bootstrap-personal-workspace.ts src/modules/workspace/infrastructure/postgres/workspace-repository.ts src/modules/commerce/domain/personal-billing-account.ts src/workflows/registration/activate-registration.ts test/component/personal-bootstrap.test.ts && git commit -m "feat(platform): bootstrap personal workspace atomically"`.

### Task 14B: Implement ProductContext and SessionAccessGrant authorization

**Repository:** `kokoro-platform`

**Files:**

- Modify: `prisma/schema.prisma`
- Create: `prisma/migrations/20260728_session_access_authorization/migration.sql`
- Create: `src/modules/authorization/domain/session-access-grant.ts`
- Create: `src/modules/authorization/application/services/exchange-product-context.ts`
- Create: `src/modules/authorization/application/services/issue-session-access-grant.ts`
- Create: `src/modules/authorization/application/services/publish-session-authorization.ts`
- Create: `src/modules/authorization/infrastructure/jose/session-access-grant-signer.ts`
- Create: `src/modules/authorization/infrastructure/postgres/session-authorization-repository.ts`
- Create: `src/interfaces/http/platform-public.ts`
- Create: `test/security/session-access-grant.test.ts`
- Create: `test/component/session-authorization-outbox.test.ts`
- Create: `test/contract/platform-public-http.test.ts`

- [ ] Write failing behavior tables for ProductWorkload+deployment resolution, artifact/release/contract mismatch, active Site/User/
  AuthSession/ProjectMembership checks, four exact audiences, explicit project/session/run resource union, five-minute maximum TTL,
  independent `grantRef`, issuer/kid/nbf/expiry, and every Site/AuthSession/Membership/authorization/restriction/credential/policy/
  revocation epoch. Browser-provided Site/subject/namespace claims must be rejected rather than ignored.
- [ ] Add race cases that revoke/suspend/transfer/bump any epoch between context exchange and grant issue; the issue transaction must
  re-lock current owner rows and emit no credential on stale facts. Credential signing occurs only after a committed immutable grant
  record exists; signing failure leaves a recoverable failed-delivery state, never an untracked live grant.
- [ ] Implement production RS256 with a dedicated Authorization key ring and JWKS/pinned-public-key delivery; no HS256 production
  fallback and no reuse of the UserSession signer key. Persist only grant metadata/digests, never raw credentials or private material.
- [ ] In the same UoW as revoke/suspend/security mutation, bump the aggregate `revocationEpoch` and append a signed durable
  authorization outbox event. Keep this owner separate from Admission: Admission may consume verified authorization facts but never
  signs browser/session transport credentials.
- [ ] Expose the Root-generated Platform public HTTP adapter with strict request/response schemas, `Cache-Control: no-store`,
  workload+UserSession dual authentication, stable safe errors, request correlation, and bounded bodies. Prove credential/log/error
  redaction and two-Site non-disclosure.
- [ ] Run the three targeted suites, generated-public contract drift, lint, typecheck and dependency audit; then commit only these
  paths. This task supplies Platform facts but does not declare Session's local revocation projection complete.

## Chunk 4 — Admin, Data Rights, Web products, and clean replacement

### Task 15: Implement Admin OIDC and typed authorization scopes

**Repository:** `kokoro-platform`

**Files:**

- Modify: `package.json`
- Modify: `pnpm-lock.yaml`

- Create: `src/modules/admin/domain/admin-principal.ts`
- Create: `src/modules/admin/domain/admin-scope.ts`
- Create: `src/modules/admin/application/services/complete-oidc-login.ts`
- Create: `src/modules/admin/application/services/authorize-admin-command.ts`
- Create: `src/interfaces/connect/admin-control.ts`
- Create: `test/security/admin-oidc.test.ts`
- Create: `test/security/admin-authorization.test.ts`

- [ ] Write failing tests for Authorization Code+PKCE, state/nonce, exact issuer/audience/redirect binding, short login transaction, key rotation, logout/revoke, and fail-closed IdP outage. Magic Link/dev headers must be rejected.
- [ ] Add table tests for Site/Global/BreakGlass, environment, region, device, command class, maker/checker separation, self-escalation, support/data-rights narrow audiences, and global-to-site explicit targeting.
- [ ] Run `pnpm vitest run test/security/admin-oidc.test.ts test/security/admin-authorization.test.ts`; confirm RED.
- [ ] Implement OIDC using `openid-client` and generated Connect handlers. Admin Web never receives a database credential and never calls repositories directly.
- [ ] Re-run targeted tests, generated-contract drift, lint, and typecheck.
- [ ] Commit in Platform: `git add -- package.json pnpm-lock.yaml src/modules/admin/domain/admin-principal.ts src/modules/admin/domain/admin-scope.ts src/modules/admin/application/services/complete-oidc-login.ts src/modules/admin/application/services/authorize-admin-command.ts src/interfaces/connect/admin-control.ts test/security/admin-oidc.test.ts test/security/admin-authorization.test.ts && git commit -m "feat(platform): secure admin identity and scopes"`.

### Task 16: Make Admin approvals, attempts, effects, and audit fail closed

**Repository:** `kokoro-platform`

**Files:**

- Modify: `prisma/schema.prisma`
- Create: `prisma/migrations/0005_admin_command_audit/migration.sql`
- Create: `src/modules/admin/domain/admin-command.ts`
- Create: `src/modules/admin/application/services/execute-admin-command.ts`
- Create: `src/modules/audit/application/services/append-admin-attempt.ts`
- Create: `src/workflows/admin-command/dispatch-admin-command.ts`
- Create: `test/component/admin-command-atomicity.test.ts`
- Create: `test/security/admin-attempt-gate.test.ts`

- [ ] Write failing tests for request→approval→execute state, approval expiry/scope/hash binding, duplicate/stale execution, local effect+success receipt+audit in one UoW, and external durable intent/observation.
- [ ] Prove every rejected attempt appends an independent durable receipt before returning; if that append is unavailable, fail closed with no business effect. Test audit outage, rollback, forged approval, self-approval, and unknown remote result.
- [ ] Run `pnpm vitest run test/component/admin-command-atomicity.test.ts test/security/admin-attempt-gate.test.ts`; confirm RED.
- [ ] Implement the independent attempt gate, local command bus/UoW, and external reconciliation path; redact secrets while retaining actor, target, policy, request, and result digests.
- [ ] Re-run targeted tests, Postgres fault injection, lint, and typecheck.
- [ ] Commit in Platform: `git add -- prisma/schema.prisma prisma/migrations/0005_admin_command_audit/migration.sql src/modules/admin/domain/admin-command.ts src/modules/admin/application/services/execute-admin-command.ts src/modules/audit/application/services/append-admin-attempt.ts src/workflows/admin-command/dispatch-admin-command.ts test/component/admin-command-atomicity.test.ts test/security/admin-attempt-gate.test.ts && git commit -m "feat(platform): make admin commands auditable"`.

### Task 17: Add Data Rights, notification, and support participant contracts

**Repository:** `kokoro-platform`

**Files:**

- Create: `src/modules/identity/application/contracts/data-rights-participant.ts`
- Create: `src/modules/workspace/application/contracts/data-rights-participant.ts`
- Create: `src/modules/site/application/contracts/data-rights-participant.ts`
- Create: `src/modules/audit/application/contracts/audit-export.ts`
- Create: `src/modules/identity/application/services/notification-outbox.ts`
- Create: `src/interfaces/connect/data-rights-participants.ts`
- Create: `test/contract/data-rights-participants.test.ts`
- Create: `test/component/data-rights-receipts.test.ts`

- [ ] Write failing contract tests for discover/plan/freeze/export/dispose/verify with subject generation, owner scope, plan hash, policy epoch, LegalHold, partial completion, retry, and signed receipt. W1 must not claim to be the cross-system Wave 7 coordinator.
- [ ] Add tests preserving minimal Support/DataRights/mandatory-inbound access during Site suspension while denying product mutation; export must be deterministic and Site-separated.
- [ ] Run `pnpm vitest run test/contract/data-rights-participants.test.ts test/component/data-rights-receipts.test.ts`; confirm RED.
- [ ] Implement owner participant adapters and notification outbox. Keep orchestration external and make every plan/verify pair generation-bound.
- [ ] Re-run targeted tests, policy tests, lint, and typecheck.
- [ ] Commit in Platform: `git add -- src/modules/identity/application/contracts/data-rights-participant.ts src/modules/workspace/application/contracts/data-rights-participant.ts src/modules/site/application/contracts/data-rights-participant.ts src/modules/audit/application/contracts/audit-export.ts src/modules/identity/application/services/notification-outbox.ts src/interfaces/connect/data-rights-participants.ts test/contract/data-rights-participants.test.ts test/component/data-rights-receipts.test.ts && git commit -m "feat(platform): add data rights participants"`.

### Task 18: Publish the Site app-kit and prove two independent Web projects

**Repository:** `kokoro-web`

**Files:**

- Create: `packages/site-app-kit/package.json`
- Create: `packages/site-app-kit/src/index.ts`
- Create: `packages/site-client/package.json`
- Create: `packages/site-client/src/generated/platform-public.ts`
- Create: `packages/site-scaffold/package.json`
- Create: `packages/site-scaffold/src/scaffold.ts`
- Create: `apps/reference-site/package.json`
- Create: `apps/reference-site/src/site-bootstrap.ts`
- Create: `test/site/site-project-isolation.test.ts`
- Create: `test/site/site-auth-journey.test.ts`
- Create: `scripts/certify-external-sites.mjs`
- Create: `packages/site-scaffold/templates/site/.github/workflows/site-ci.yml`
- Create generated sanitized report: `test/reports/external-sites/site-alpha.json`
- Create generated sanitized report: `test/reports/external-sites/site-beta.json`
- Create generated sanitized report: `test/reports/external-sites/summary.json`
- Modify: `pnpm-workspace.yaml`
- Modify: `pnpm-lock.yaml`

- [ ] First add a minimal test-runner package/script so the red command resolves the intended tests; do not depend on an undeclared
  workspace-root Vitest binary. Write failing tests for one orchestrator that packs exact app-kit/client versions and generates Site
  Alpha/Beta into separate temporary Git repositories with independent package names, CI configs, frozen lockfiles, commits,
  artifact manifests, deployment configs, release IDs, domain bindings, and signed contract floors.
- [ ] Assert no runtime Host-based theme switch, shared account/session, raw Platform URL construction, Admin import, or database client. Exercise registration→verify→explicit login→MFA→session revoke through the generated Platform client with isolated cookies.
- [ ] Run `pnpm --filter @kokoro/site-scaffold --fail-if-no-match test -- --run site-project-isolation.test.ts site-auth-journey.test.ts`; confirm RED for missing orchestration behavior, never for a missing filter/binary.
- [ ] Implement the versioned app-kit, generated Site client, scaffold, and reference Site. Use Auth.js only as the Web session/cookie integration surface; Platform remains credential authority.
- [ ] Implement `certify-external-sites.mjs` as the single lifecycle owner: pack exact packages → generate both repos → git
  init/commit → frozen clean install → independent CI command/build → launch two deployments → activate exact Platform bindings →
  cross-Site/Host/cookie/auth journey → rollback Alpha and Beta independently → shutdown/cleanup. Persist only sanitized package,
  lock, commit, artifact, binding, deployment, isolation and rollback digests/results in the three declared reports.
- [ ] Run `pnpm --filter @kokoro/site-scaffold --fail-if-no-match test`, then
  `node scripts/certify-external-sites.mjs --output test/reports/external-sites`, followed by Web lint/typecheck/full test. Confirm
  both deployments and independent rollback receipts; do not add Wave 3 Chat/session-client behavior here.
- [ ] Commit only declared Web paths with `git add -- packages/site-app-kit/package.json packages/site-app-kit/src/index.ts packages/site-client/package.json packages/site-client/src/generated/platform-public.ts packages/site-scaffold/package.json packages/site-scaffold/src/scaffold.ts packages/site-scaffold/templates/site/.github/workflows/site-ci.yml apps/reference-site/package.json apps/reference-site/src/site-bootstrap.ts test/site/site-project-isolation.test.ts test/site/site-auth-journey.test.ts scripts/certify-external-sites.mjs test/reports/external-sites/site-alpha.json test/reports/external-sites/site-beta.json test/reports/external-sites/summary.json pnpm-workspace.yaml pnpm-lock.yaml`, then commit.

### Task 19: Remove legacy Payment, MySQL, self-RPC, and owner duplicates after consumer cutover

**Repository:** `kokoro-platform` first; Root contract scans second

**Files:**

- Create: `test/architecture/wave1-clean-replacement.test.ts`
- Create: `scripts/clean-replacement/stage-allowlist.mjs`
- Create generated reviewed allowlist: `scripts/clean-replacement/wave1-delete-allowlist.txt`
- Modify: `package.json`
- Modify: `pnpm-workspace.yaml`
- Modify: `pnpm-lock.yaml`
- Delete after preflight: `kokoro-payment/**`
- Delete after preflight: `kokoro-model/**`
- Delete after preflight: `kokoro-site/**`
- Delete after preflight: `kokoro-user/**`
- Delete after preflight: `kokoro-platform-admin/**`
- Modify: `INDEX.md`
- Modify: `README.md`
- Root create: `scripts/contract/check-wave1-clean-replacement.mjs`
- Root create: `scripts/contract/check-wave1-clean-replacement.test.mjs`

- [ ] Inventory every legacy route, env key, process, package, schema, CI entry, import, dependency, deployment manifest, and documentation claim; encode the expected replacement owner before deleting anything.
- [ ] Write failing seven-layer Payment closure tests: no UI/link, route/descriptor, server handler, package/process, secret/env, outbound provider egress, database row/fact, or runtime capability. Stable disabled errors are allowed only on explicitly contracted non-purchase discovery surfaces.
- [ ] Add failing scans for MySQL drivers/URLs, local self-RPC, duplicate Site/User/Admin/Model owners, Host theme fallback, Magic Link/dev auth, and compatibility adapters. Assert W2A-owned Redeem/Credit surfaces remain unreachable until W2A qualification.
- [ ] Run Platform architecture tests and Root scan tests; confirm RED against the legacy tree.
- [ ] Implement `stage-allowlist.mjs` to generate a reviewed, newline-delimited list of every tracked legacy file from the five
  declared roots, compare that list to the frozen preflight inventory, reject directories/globs/untracked paths/path traversal, and
  stage deletions one exact path at a time with `git add -- <path>`. Complete all consumer cutovers and preflight parity/evidence,
  review and freeze `wave1-delete-allowlist.txt`, then remove only those files. Do not delete historical database volumes or
  external financial records.
- [ ] Run `pnpm lint && pnpm typecheck && pnpm test` in Platform and `node --test scripts/contract/check-wave1-clean-replacement.test.mjs` in Root; confirm legacy consumer count and forbidden surface count are zero.
- [ ] Stage the non-deletion files exactly with
  `git add -- package.json pnpm-workspace.yaml pnpm-lock.yaml test/architecture/wave1-clean-replacement.test.ts scripts/clean-replacement/stage-allowlist.mjs scripts/clean-replacement/wave1-delete-allowlist.txt INDEX.md README.md`.
  Then run
  `node scripts/clean-replacement/stage-allowlist.mjs --allowlist scripts/clean-replacement/wave1-delete-allowlist.txt --stage-deletions --assert-index-exact package.json pnpm-workspace.yaml pnpm-lock.yaml test/architecture/wave1-clean-replacement.test.ts scripts/clean-replacement/stage-allowlist.mjs scripts/clean-replacement/wave1-delete-allowlist.txt INDEX.md README.md`.
  The script must fail if the staged set differs from the explicit static paths plus exact allowlist entries; only then commit the
  deletion. Commit the Root scanner separately with
  `git add -- scripts/contract/check-wave1-clean-replacement.mjs scripts/contract/check-wave1-clean-replacement.test.mjs`.

## Chunk 5 — Production qualification and atomic promotion

### Task 20: Prove backup/restore, load, two-Site isolation, DR, clean clone, and release provenance

**Repository:** Root (orchestration/evidence), with child verification only

**Files:**

- Modify gitlink: `kokoro-platform`
- Modify gitlink: `kokoro-web`
- Create: `scripts/verification/wave1-qualification.mjs`
- Create: `scripts/verification/wave1-qualification.test.mjs`
- Create: `docs/reports/evidence/wave-1/platform-postgres-uow.md`
- Create: `docs/reports/evidence/wave-1/identity-security-journeys.md`
- Create: `docs/reports/evidence/wave-1/site-lifecycle-two-projects.md`
- Create: `docs/reports/evidence/wave-1/admin-security-and-audit.md`
- Create: `docs/reports/evidence/wave-1/model-control-cutover.md`
- Create: `docs/reports/evidence/wave-1/payment-closure.md`
- Create: `docs/reports/evidence/wave-1/platform-deployables-slo-load-and-dr.md`
- Create: `docs/reports/evidence/wave-1/ga-semantic-non-regression.md`
- Create: `docs/reports/evidence/wave-1/wave-1-clean-replacement-inventory.md`
- Modify: `config/repository/compatibility-matrix.json`
- Modify: `config/repository/federated-repositories.json`
- Modify in follow-up evidence/provenance commit: `config/repository/bom.json`
- Modify: `docs/task.md`

- [ ] Write failing qualification modes: `--candidate` requires exact child SHAs, contract/artifact/report digests, PostgreSQL 18,
  independent Platform/Session databases/roles, two independent Site artifacts, GA golden bytes and no Payment/MySQL surface;
  `--rollback-of` verifies restored pins/registry/Infra; `--release` additionally requires every Wave 1 evidence document populated
  from machine-readable reports. Candidate verification must not require evidence that can only be written after its own clone run.
- [ ] As main integrator, inspect existing containers and leases. Start or reconcile exactly one default Infra stack only if needed; do not permit subagents to create stacks. Stop surplus test containers before proceeding, without pruning volumes/images/developer data.
- [ ] Run child repository gates from clean states: Platform `pnpm audit --audit-level high && pnpm lint && pnpm typecheck && pnpm test`; Web `pnpm audit --audit-level high && pnpm lint && pnpm typecheck && pnpm test && pnpm build`; Root contract/infra/repository suites; GA read-only golden-byte and forbidden-field tests.
- [ ] Run real PostgreSQL qualification: fresh migrate, rollback-safe failure injection, backup while active, restore into an isolated leased database, row/digest parity, point-in-time/operational recovery procedure, API/Worker/migrator independent restart, and connection/timeout exhaustion behavior.
- [ ] Run production-like journeys across Site Alpha/Beta: complete Identity/MFA/recovery/session flows; Site request/provision/activate/drain/rollback/suspend/resume/decommission; Admin approval/rejection/audit; ModelControl selection/fallback; Data Rights participant plan/verify; cross-Site leakage and stale-epoch negative tests.
- [ ] Run load/SLO checks with at least 100 Sites and 100 admission/policy decisions per second at the agreed fixture size; record p50/p95/p99, error budget, database saturation, queue lag, reconciliation latency, and recovery thresholds. Averages alone do not qualify.
- [ ] Re-run `node scripts/wave1/preflight.mjs --verify-baseline .git/kokoro-wave1/baseline.json --ga-only`. Require the
  original Agent SHA, empty full porcelain status including untracked files, identical SHA-256 for both control files, and
  `run.request`/`run.cancel` golden-byte tests. Generated parity alone is insufficient.
- [ ] Stop surplus/default verification containers through the Root manager; record final service/image/profile/port/volume/data
  inventory proving PostgreSQL replaced only MySQL and Redis/Mongo/MinIO remain exact. Preserve all volumes/images/developer data.
- [ ] Finalize Platform and Web child commits first. Run each child’s complete local and remote CI, push the exact commits, create/push
  unique annotated release tags, and record commit/tag/artifact digests. Before any Root candidate commit, use the qualification
  verifier to fetch each tag/commit from its configured remote into an isolated temporary Git object database and require
  `cat-file -e <sha>^{commit}` plus annotated-tag target equality. A local child object, branch ref, or tag that the remote cannot
  supply is a hard stop; recursive-clone qualification may never rely on an unpushed submodule SHA.
- [ ] Prepare compatibility/federated changes and exact remotely retrievable child gitlinks, then create a local candidate promotion commit before
  any clean-clone claim. Stage only declared paths:

```bash
git add -- kokoro-platform kokoro-web config/repository/compatibility-matrix.json config/repository/federated-repositories.json scripts/verification/wave1-qualification.mjs scripts/verification/wave1-qualification.test.mjs
git commit -m "release(root): candidate wave1 platform foundation"
wave1_candidate_sha=$(git rev-parse HEAD)
```

- [ ] Verify that exact SHA in a recursive local clone, then create a second clone and rehearse rollback as a new revert commit:

```bash
wave1_source_root=$(git rev-parse --show-toplevel)
wave1_candidate_clone=$(mktemp -d)
wave1_revert_clone=$(mktemp -d)
git clone --recurse-submodules "$wave1_source_root" "$wave1_candidate_clone/repo"
git -C "$wave1_candidate_clone/repo" checkout --detach "$wave1_candidate_sha"
git -C "$wave1_candidate_clone/repo" submodule update --init --recursive
node "$wave1_candidate_clone/repo/scripts/verification/wave1-qualification.mjs" --repo "$wave1_candidate_clone/repo" --candidate "$wave1_candidate_sha" --baseline "$wave1_source_root/.git/kokoro-wave1/baseline.json"
git clone --recurse-submodules "$wave1_source_root" "$wave1_revert_clone/repo"
git -C "$wave1_revert_clone/repo" checkout --detach "$wave1_candidate_sha"
git -C "$wave1_revert_clone/repo" switch -c wave1-rollback-rehearsal
git -C "$wave1_revert_clone/repo" revert --no-edit "$wave1_candidate_sha"
git -C "$wave1_revert_clone/repo" submodule update --init --recursive
node "$wave1_candidate_clone/repo/scripts/verification/wave1-qualification.mjs" --repo "$wave1_revert_clone/repo" --rollback-of "$wave1_candidate_sha" --baseline "$wave1_source_root/.git/kokoro-wave1/baseline.json"
```

- [ ] Persist sanitized candidate/revert SHAs, exact command results, GA SHA/status/two hashes/golden bytes, external-Site reports,
  Postgres/DR/SLO evidence and preserved Infra inventory in the declared evidence files. Remove only validated temporary clone
  directories. Have `wave1-qualification.mjs` emit the canonical machine-readable runtime gate at
  `.git/kokoro-wave1/runtime-evidence.json`; validate that it binds the candidate SHA, child artifact/tag digests, compatibility
  assertions, evidence inputs and preserved Infra inventory. Generate and verify the BOM only after `wave1_candidate_sha` exists:

```bash
node scripts/repository/generate-bom.mjs --promotion-commit "$wave1_candidate_sha" --runtime-evidence .git/kokoro-wave1/runtime-evidence.json
node scripts/repository/generate-bom.mjs --check --promotion-commit "$wave1_candidate_sha"
```

  Create the follow-up evidence/provenance commit with exact paths:

```bash
git add -- docs/reports/evidence/wave-1/platform-postgres-uow.md docs/reports/evidence/wave-1/identity-security-journeys.md docs/reports/evidence/wave-1/site-lifecycle-two-projects.md docs/reports/evidence/wave-1/admin-security-and-audit.md docs/reports/evidence/wave-1/model-control-cutover.md docs/reports/evidence/wave-1/payment-closure.md docs/reports/evidence/wave-1/platform-deployables-slo-load-and-dr.md docs/reports/evidence/wave-1/ga-semantic-non-regression.md docs/reports/evidence/wave-1/wave-1-clean-replacement-inventory.md docs/task.md config/repository/bom.json
git commit -m "release(wave1): record qualification and BOM provenance"
```

- [ ] Only after both local Root commits are reviewed, push the Root candidate branch; child commits and annotated tags are already
  remote-verified prerequisites. Root remote CI
  must hydrate the exact pins using the user-owned `KOKORO_SUBMODULE_TOKEN` and pass both commits. Create/push the Root BOM tag only
  after that exact remote CI is green; missing token/CI is a blocker, never an exception.

## Definition of Done

Wave 1 is DONE only when every Task 0–20 commit, including both 2A and 2B, and Task 20 evidence pass from a recursive clean clone. In particular:

- Platform has one PostgreSQL authority, local owner ports/UoW, no local self-RPC, no raw cross-owner Prisma access, no MySQL active path, and no duplicate legacy owner process.
- Identity is a complete Site-bound lifecycle, not only signup/login; personal Workspace/BillingAccount shell bootstrap is atomic and does not trespass on W2A facts.
- Site is a full control-plane lifecycle backed by immutable release provenance and two truly independent Web projects, not one Host-switched multi-brand artifact.
- Admin has OIDC, typed axes, maker/checker, independent rejected-attempt durability, atomic local effects, and no database/bypass path from Web.
- ModelControl provides one base inventory plus product/Site policy, deterministic fallback, and no legacy model-service consumers; Model Gateway remains a remote execution boundary.
- Payment acquisition is absent across all seven layers. Redeem/Credit and `chat.execution.prepare` remain unavailable until their owner Waves qualify.
- Session and Web are not declared globally complete by this Wave: W3 must independently qualify admission, runtime projections, resumable streams, multi-tab behavior, attachment/tool/HITL UX, and chat BFF isolation. Wave 1 only supplies their approved Site/Identity/Policy foundations.
- GA graph/checkpoint/control/terminal/handoff semantics and `run.request`/`run.cancel` bytes are unchanged.
- A root-owned default Infra lifecycle, clean-clone replay, backup/restore/DR, two-Site isolation, SLO/load results, CI, artifacts, tags, pins, BOM, and rollback evidence all agree on the same immutable digests.
