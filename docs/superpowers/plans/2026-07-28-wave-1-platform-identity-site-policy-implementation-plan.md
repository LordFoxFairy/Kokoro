# Wave 1 Platform / Identity / Site / Policy Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a production-qualified PostgreSQL Platform control plane with complete Site-bound Identity, personal Workspace bootstrap, immutable Site release lifecycle, secure Admin operations, local ModelControl ownership, Data Rights participation, redeem-only Payment closure, two independent Site projects, and backup/restore/DR evidence—without changing GA runtime semantics.

**Architecture:** Root remains contract, Infra, compatibility, BOM, and pin-promotion authority. `kokoro-platform` is one deployable bounded context using a PostgreSQL modular monolith: owner modules collaborate through application ports and a single opaque Unit of Work, while true remote systems use generated Connect/HTTP contracts plus durable intent/reconciliation. Each public Site is an independent Web repository/artifact/deployment that consumes signed app-kit and generated clients. W2A exclusively owns Redeem/Fulfillment/Credit facts; W3 owns Session admission and Chat Web runtime. GA remains an opaque namespace consumer and its existing control wire is frozen.

**Tech Stack:** TypeScript 5.9, Node.js 22, pnpm 11, PostgreSQL 18, Prisma 7, ConnectRPC/Protobuf, OpenAPI 3.1, Next.js/Auth.js, Vitest, Node test runner, Playwright, Buf, Docker Compose (single shared default Infra lifecycle only).

---

## Execution rules and dependency graph

- Root, `kokoro-platform`, and `kokoro-web` are separate repositories. Every task commits in its owning repository; only Task 20 promotes child pins in Root.
- Tasks 1–19 MUST NOT start a private Docker/Compose stack. Unit and contract tests run without containers; PostgreSQL component tests reuse the single Root-managed default Infra instance through a leased database/role.
- Only the Task 20 integrator may start or reconcile the default Infra stack. After verification it stops surplus containers; it never prunes or deletes volumes, images, or developer data.
- No task edits `kokoro-agent`. GA verification is read-only: golden-byte, forbidden-field, and compatibility assertions only.
- `chat.execution.prepare`, Redeem routes, and Credit admission remain absent until both their owner Waves are independently qualified. A placeholder, compatibility route, or declared-but-unimplemented descriptor is a failure.
- Suggested parallel cuts after Tasks 1–5 establish contracts/storage: Site (7–10), Identity/Workspace (11–14), and Admin/Data Rights (15–17). ModelControl (6) and Web (18) can run independently once their contracts are frozen. Task 19 follows consumer cutover; Task 20 is serial integration.

## Chunk 1 — Root authority and Platform kernel

### Task 1: Freeze Wave 1 public and privileged contracts

**Repository:** Root

**Files:**

- Create: `contract/openapi/platform-public-v1.yaml`
- Create: `contract/proto/kokoro/platform/site/v1/site_lifecycle.proto`
- Create: `contract/proto/kokoro/platform/identity/v1/admin_identity.proto`
- Create: `contract/proto/kokoro/platform/admin/v2/admin_control.proto`
- Modify: `contract/buf.yaml`
- Modify: `contract/generate.mjs`
- Modify: `contract/registry/boundaries.yaml`
- Modify: `contract/tests/test_buf_contract.py`
- Modify: `contract/tests/test_generate.py`
- Create: `scripts/contract/check-wave1-surface.mjs`
- Create: `scripts/contract/check-wave1-surface.test.mjs`

- [ ] Write failing contract tests for Site-bound registration/login/session management, Site lifecycle/release commands, typed Admin scope/axes/approval, operation receipts, stable error codes, request IDs, idempotency keys, and generated-only consumer artifacts. Assert that no Payment purchase route and no `chat.execution.prepare` descriptor exists.
- [ ] Run `python -m pytest contract/tests/test_buf_contract.py contract/tests/test_generate.py -q && node --test scripts/contract/check-wave1-surface.test.mjs`; confirm RED because the Wave 1 schemas and registry edges are missing.
- [ ] Add additive versioned contracts and exact boundary registry ownership. Keep public browser HTTP separate from privileged ConnectRPC; do not expose raw database identifiers or internal policy records.
- [ ] Generate deterministic mirrors with `pnpm --dir contract buf:lint && pnpm --dir contract buf:generate`; ensure a second generation produces no diff.
- [ ] Run the targeted tests plus `node scripts/contract/check-boundary-coverage.mjs`; confirm all new provider/consumer edges match the exact boundary, not merely the repository pair.
- [ ] Commit in Root: `git add contract scripts/contract && git commit -m "feat(contract): freeze wave1 platform surfaces"`.

### Task 2: Replace the default MySQL Infra contract with isolated PostgreSQL databases

**Repository:** Root

**Files:**

- Modify: `docker-compose.infra.yml`
- Modify: `config/repository/infrastructure-policy.yaml`
- Modify: `scripts/infra/manager.mjs`
- Modify: `scripts/infra/manager.test.mjs`
- Modify: `scripts/infra/scope.mjs`
- Modify: `scripts/infra/scope.test.mjs`
- Modify: `scripts/infra/inventory.mjs`
- Modify: `scripts/infra/inventory.test.mjs`
- Modify: `scripts/infra/INDEX.md`

- [ ] Add failing policy tests requiring PostgreSQL 18 in `platform`/`full`, separate `kokoro_platform` and `kokoro_session` databases, separate runtime/migrator/test roles, leased test schemas/databases, bounded health checks, and zero MySQL runtime contexts.
- [ ] Add failing lifecycle tests proving `stop`/lease cleanup never invokes volume/image prune or removes named developer data; prove only the Root manager owns default-stack lifecycle.
- [ ] Run `node --test scripts/infra/*.test.mjs`; confirm RED on MySQL service/profile/lease expectations.
- [ ] Implement the PostgreSQL service, roles, health check, manager inventory, and lease behavior. Remove MySQL from active profiles without deleting historical volumes.
- [ ] Re-run the Node suite and `node scripts/infra/inventory.mjs --check`; inspect rendered Compose config only with `docker compose -f docker-compose.infra.yml config`—do not start containers in this task.
- [ ] Commit in Root: `git add docker-compose.infra.yml config/repository/infrastructure-policy.yaml scripts/infra && git commit -m "feat(infra): standardize isolated postgres authority"`.

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
- [ ] Commit in Platform: `git add prisma prisma.config.ts src/infrastructure src/process package.json pnpm-lock.yaml test && git commit -m "feat(platform): establish postgres runtime foundation"`.

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
- [ ] Commit in Platform: `git add src/shared test eslint.config.mjs && git commit -m "feat(platform): add transactional module kernel"`.

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
- [ ] Commit in Platform: `git add src/shared/security-context src/modules/policy test && git commit -m "feat(platform): enforce effect point policy"`.

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
- [ ] Commit in Platform: `git add src/modules/model-control scripts/model-control test && git commit -m "feat(platform): make model control canonical"`.

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
- [ ] Commit in Platform: `git add prisma src/modules/site test/component/site-aggregate.test.ts && git commit -m "feat(platform): add immutable site releases"`.

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
- [ ] Commit in Platform: `git add src/workflows/site-lifecycle src/modules/site/application src/interfaces/connect test && git commit -m "feat(platform): orchestrate site provisioning"`.

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
- [ ] Commit in Platform: `git add src/workflows/site-lifecycle src/modules/site/application test && git commit -m "feat(platform): qualify site release lifecycle"`.

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
- [ ] Commit in Platform: `git add src/workflows/site-lifecycle src/modules/site/domain test && git commit -m "feat(platform): close site disposition lifecycle"`.

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
- [ ] Commit in Platform: `git add prisma src/modules/identity src/interfaces/http test && git commit -m "feat(platform): add site bound registration"`.

### Task 12: Implement password login, TOTP, recovery codes, and session issuance

**Repository:** `kokoro-platform`

**Files:**

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
- [ ] Commit in Platform: `git add src/modules/identity test/security package.json pnpm-lock.yaml && git commit -m "feat(platform): complete password and mfa login"`.

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
- [ ] Commit in Platform: `git add src/modules/identity src/interfaces/http test/security && git commit -m "feat(platform): close identity recovery and sessions"`.

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
- [ ] Commit in Platform: `git add prisma src/modules/workspace src/modules/commerce src/workflows/registration test && git commit -m "feat(platform): bootstrap personal workspace atomically"`.

## Chunk 4 — Admin, Data Rights, Web products, and clean replacement

### Task 15: Implement Admin OIDC and typed authorization scopes

**Repository:** `kokoro-platform`

**Files:**

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
- [ ] Commit in Platform: `git add src/modules/admin src/interfaces/connect test/security package.json pnpm-lock.yaml && git commit -m "feat(platform): secure admin identity and scopes"`.

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
- [ ] Commit in Platform: `git add prisma src/modules/admin src/modules/audit src/workflows/admin-command test && git commit -m "feat(platform): make admin commands auditable"`.

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
- [ ] Commit in Platform: `git add src/modules src/interfaces/connect test && git commit -m "feat(platform): add data rights participants"`.

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
- Modify: `pnpm-workspace.yaml`

- [ ] Write failing tests that generate Site Alpha and Site Beta into separate temporary Git repositories with independent package names, lockfiles, CI, artifact manifests, deployment config, release IDs, domain bindings, and signed app-kit/contract floors.
- [ ] Assert no runtime Host-based theme switch, shared account/session, raw Platform URL construction, Admin import, or database client. Exercise registration→verify→explicit login→MFA→session revoke through the generated Platform client with isolated cookies.
- [ ] Run `pnpm vitest run test/site/site-project-isolation.test.ts test/site/site-auth-journey.test.ts`; confirm RED.
- [ ] Implement the versioned app-kit, generated Site client, scaffold, and reference Site. Use Auth.js only as the Web session/cookie integration surface; Platform remains credential authority.
- [ ] Re-run targeted tests, `pnpm lint`, `pnpm typecheck`, `pnpm test`, and build each generated fixture separately. Do not add Wave 3 Chat/session-client behavior here.
- [ ] Commit in Web: `git add packages apps/reference-site test pnpm-workspace.yaml pnpm-lock.yaml && git commit -m "feat(web): publish isolated site application kit"`.

### Task 19: Remove legacy Payment, MySQL, self-RPC, and owner duplicates after consumer cutover

**Repository:** `kokoro-platform` first; Root contract scans second

**Files:**

- Create: `test/architecture/wave1-clean-replacement.test.ts`
- Modify: `package.json`
- Modify: `pnpm-workspace.yaml`
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
- [ ] Complete all consumer cutovers, run preflight parity/evidence, then remove legacy packages and obsolete deploy/docs/config in one bounded deletion commit. Do not delete historical database volumes or external financial records.
- [ ] Run `pnpm lint && pnpm typecheck && pnpm test` in Platform and `node --test scripts/contract/check-wave1-clean-replacement.test.mjs` in Root; confirm legacy consumer count and forbidden surface count are zero.
- [ ] Commit Platform deletion: `git add -A && git commit -m "refactor(platform): complete wave1 clean replacement"`; then commit Root scanner separately: `git add scripts/contract && git commit -m "test(contract): enforce wave1 clean replacement"`.

## Chunk 5 — Production qualification and atomic promotion

### Task 20: Prove backup/restore, load, two-Site isolation, DR, clean clone, and release provenance

**Repository:** Root (orchestration/evidence), with child verification only

**Files:**

- Create: `scripts/verification/wave1-qualification.mjs`
- Create: `scripts/verification/wave1-qualification.test.mjs`
- Create: `docs/evidence/wave-1/platform-postgres-uow.md`
- Create: `docs/evidence/wave-1/identity-security-journeys.md`
- Create: `docs/evidence/wave-1/site-lifecycle-two-projects.md`
- Create: `docs/evidence/wave-1/admin-security-and-audit.md`
- Create: `docs/evidence/wave-1/model-control-cutover.md`
- Create: `docs/evidence/wave-1/payment-closure.md`
- Create: `docs/evidence/wave-1/platform-deployables-slo-load-and-dr.md`
- Create: `docs/evidence/wave-1/ga-semantic-non-regression.md`
- Create: `docs/evidence/wave-1/wave-1-clean-replacement-inventory.md`
- Modify: `config/repository/compatibility-matrix.json`
- Modify: `config/repository/federated-repositories.json`
- Modify: `config/repository/bom.json`
- Modify: `docs/task.md`

- [ ] Write failing qualification tests that require exact child SHAs, contract/artifact/evidence digests, PostgreSQL 18, independent Platform/Session databases and roles, two independent Site artifacts, GA golden-byte evidence, no Payment/MySQL surface, and every Wave 1 evidence document populated from machine-readable reports.
- [ ] As main integrator, inspect existing containers and leases. Start or reconcile exactly one default Infra stack only if needed; do not permit subagents to create stacks. Stop surplus test containers before proceeding, without pruning volumes/images/developer data.
- [ ] Run child repository gates from clean states: Platform `pnpm audit --audit-level high && pnpm lint && pnpm typecheck && pnpm test`; Web `pnpm audit --audit-level high && pnpm lint && pnpm typecheck && pnpm test && pnpm build`; Root contract/infra/repository suites; GA read-only golden-byte and forbidden-field tests.
- [ ] Run real PostgreSQL qualification: fresh migrate, rollback-safe failure injection, backup while active, restore into an isolated leased database, row/digest parity, point-in-time/operational recovery procedure, API/Worker/migrator independent restart, and connection/timeout exhaustion behavior.
- [ ] Run production-like journeys across Site Alpha/Beta: complete Identity/MFA/recovery/session flows; Site request/provision/activate/drain/rollback/suspend/resume/decommission; Admin approval/rejection/audit; ModelControl selection/fallback; Data Rights participant plan/verify; cross-Site leakage and stale-epoch negative tests.
- [ ] Run load/SLO checks with at least 100 Sites and 100 admission/policy decisions per second at the agreed fixture size; record p50/p95/p99, error budget, database saturation, queue lag, reconciliation latency, and recovery thresholds. Averages alone do not qualify.
- [ ] Create a recursive clean clone, hydrate exact pins, regenerate contracts, verify both Site artifacts, and rehearse rollback to the previous BOM. Root remote CI must be green; missing `KOKORO_SUBMODULE_TOKEN` is a release blocker, not an exception.
- [ ] Stop surplus/default verification containers through the Root manager; record final `docker ps` inventory. Preserve volumes/images/developer data.
- [ ] Tag and push each child repository only after its independent CI is green. Update Root gitlinks, compatibility matrix, federated roles, BOM, and evidence digests atomically; run the full Root gate again.
- [ ] Commit Root promotion: `git add kokoro-platform kokoro-web config/repository docs scripts/verification && git commit -m "release(root): qualify wave1 platform foundation"`. Create the Root BOM tag only after remote Root CI is green.

## Definition of Done

Wave 1 is DONE only when all 20 task commits and Task 20 evidence pass from a recursive clean clone. In particular:

- Platform has one PostgreSQL authority, local owner ports/UoW, no local self-RPC, no raw cross-owner Prisma access, no MySQL active path, and no duplicate legacy owner process.
- Identity is a complete Site-bound lifecycle, not only signup/login; personal Workspace/BillingAccount shell bootstrap is atomic and does not trespass on W2A facts.
- Site is a full control-plane lifecycle backed by immutable release provenance and two truly independent Web projects, not one Host-switched multi-brand artifact.
- Admin has OIDC, typed axes, maker/checker, independent rejected-attempt durability, atomic local effects, and no database/bypass path from Web.
- ModelControl provides one base inventory plus product/Site policy, deterministic fallback, and no legacy model-service consumers; Model Gateway remains a remote execution boundary.
- Payment acquisition is absent across all seven layers. Redeem/Credit and `chat.execution.prepare` remain unavailable until their owner Waves qualify.
- Session and Web are not declared globally complete by this Wave: W3 must independently qualify admission, runtime projections, resumable streams, multi-tab behavior, attachment/tool/HITL UX, and chat BFF isolation. Wave 1 only supplies their approved Site/Identity/Policy foundations.
- GA graph/checkpoint/control/terminal/handoff semantics and `run.request`/`run.cancel` bytes are unchanged.
- A root-owned default Infra lifecycle, clean-clone replay, backup/restore/DR, two-Site isolation, SLO/load results, CI, artifacts, tags, pins, BOM, and rollback evidence all agree on the same immutable digests.
