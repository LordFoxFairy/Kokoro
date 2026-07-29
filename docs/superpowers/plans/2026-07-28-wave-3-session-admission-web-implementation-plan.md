# Wave 3 Session Admission and Site Web Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved General Chat closure with Platform-owned Admission, PostgreSQL-backed Session projections, resumable HTTP/SSE, brandless Web packages, and independently buildable Site Web artifacts while keeping GA byte-for-byte unchanged.

**Architecture:** Root owns the only cross-repository wire contracts and promotion gate. `kokoro-platform` implements Admission as a local Platform workflow over the Wave 1 PostgreSQL/UoW and Wave 2A Credit authority; `kokoro-session` owns conversation/projection/outbox state in its own PostgreSQL database and dispatches the existing GA wire only after a committed authorization receipt. `kokoro-web` publishes brandless packages and a reference harness; production-like Site fixtures are generated as independent temporary Git repositories with their own locks and artifacts.

**Tech Stack:** Node.js 24 LTS, TypeScript 5.9, Zod 4, Vitest 4.1, Prisma 7, PostgreSQL 18, ConnectRPC 2.1.2/Protobuf, Redis Streams, Next.js 16.2, React 19.2, `@assistant-ui/react@0.14.28`, Playwright, pnpm 11 for Platform/Web and the existing isolated Session package manager until the separate toolchain migration.

---

## Preconditions and non-negotiable gates

- Approved spec: `docs/superpowers/specs/2026-07-28-wave-3-session-admission-projection-design.md`; Task 0 must prove its
  approved/authorized machine-readable state before Task 1. Prose in this plan cannot waive that gate.
- Wave 1 must have landed `kokoro-platform/prisma/schema.prisma`, `src/shared/unit-of-work`, security context, Site/Project/Identity ports, PostgreSQL 18, and removal of same-domain self-RPC.
- Wave 2A must have landed the authoritative execution budget root, root Hold, Credit Journal, Grant allocation, and typed Credit application ports. Wave 3 references them; it does not create a second balance/Hold implementation.
- Root contract files have one writer. The execution DAG is fixed:

```text
Root: Task 0 → Task 1 → Task 2 (generated-mirror handoff)
                          ├→ Platform: Task 3 → 4 → 5 → 6 ─┐
                          ├→ Session:  Task 7 → 8 → 9 → 10 → 11 → 12 → 13 ─┤→ Task 19
                          └→ Web:      Task 14 → 15 → 16 → 17 → 18 ────────┘
```

  Lanes may run in parallel only after Task 2 has committed the relevant mirror in that child. Within a child, tasks are serial
  and exactly one worker owns its worktree/index/lockfile. During Task 2 the generator worker has exclusive write ownership of all
  mirror target paths; child lanes start only after the generated commit SHA/digest handoff is recorded.
- Use the one default Infra stack. Do not create a Compose project or container stack per worker. Real PostgreSQL tests use isolated database/schema names and remove test state after completion.
- Task 0 records SHA/status for Root and all four children. Every task requires a clean baseline and may stage only its declared
  paths with `git add -- <exact-paths>`; `git add -A`, broad directory staging, and another worker's changes are forbidden.
- Task 0 also records the GA baseline SHA/status, SHA-256 for `contract/spec/control.yaml` and
  `kokoro-agent/src/kokoro_agent/contract/control.py`, and canonical golden-byte SHA-256 values for existing `run.request` and
  `run.cancel` envelopes. Every chunk, candidate clone, rollback clone, final evidence HEAD, and release gate require all values to
  match and the full Agent porcelain status, including untracked files, to remain empty.
- Every task follows red → focused green → local suite → commit. A worker does not update root gitlinks; the main integrator promotes pins only in Task 19.

## File ownership map

| Surface | New/changed ownership |
|---|---|
| Root contract | `contract/proto/kokoro/platform/admission/v1/admission.proto`, Session HTTP/events specs, registry, generator, compatibility scenario |
| Platform | `src/workflows/run-admission/**`, `src/interfaces/connect/admission/**`, shared receipt/outbox/UoW integration, Platform Prisma schema |
| Session | `prisma/**`, `src/store/postgres/**`, conversation/application commands, Admission client/outboxes, projection/SSE/auth |
| Web | `packages/session-client`, `packages/chat-surface`, `packages/bff-runtime`, `packages/site-scaffold`, `apps/user` reference harness |
| External Site fixture | Generated into OS temp directories by the scaffold test; never added to root workspace or treated as a production repository |
| GA | No files. Existing `contract/spec/control.yaml` and generated GA mirror remain byte-identical. |

### Task 0: Install and pass the executable Wave preflight

**Repository:** Root

**Files:**
- Create: `scripts/wave3/preflight.mjs`
- Create: `scripts/wave3/preflight.test.mjs`
- Create at runtime, never commit: `.git/kokoro-wave3/baseline.json`

- [ ] **Step 1: Write the failing gate tests**

Use isolated fixtures to prove the gate rejects: any Wave 1/W2A/W3 artifact not approved or
`implementationAuthorized!=true`; missing/mismatched evidence digest; absent required PostgreSQL migration/UoW/security/Credit
ports; dirty Root/child worktree; unexpected child pin; missing generated mirror; and missing required runtime port declaration.
The passing fixture writes immutable Root/four-child SHAs, statuses, required evidence digests, migration/port inventory, the two
GA control SHA-256 hashes, and canonical `run.request`/`run.cancel` golden-byte SHA-256 hashes to the baseline file. Fixtures must
independently mutate each golden envelope and prove fail-closed comparison rather than merely rerunning code generation.

- [ ] **Step 2: Run the red test**

Run: `node --test scripts/wave3/preflight.test.mjs`

Expected: FAIL because the executable gate does not exist.

- [ ] **Step 3: Implement the minimum fail-closed gate**

Read machine-readable status/evidence rather than matching narrative prose. Validate Wave 1/W2A/W3 approval and authorization,
evidence bundle digests, PostgreSQL migrations, required application ports, Root pins, generated contract digests, clean worktrees,
and canonical GA golden bytes. Never mutate a child, migration, evidence file, or pin. Atomically write only
`.git/kokoro-wave3/baseline.json`.

- [ ] **Step 4: Verify the gate and stop if the real repository is not ready**

Run: `node --test scripts/wave3/preflight.test.mjs && node scripts/wave3/preflight.mjs --write-baseline .git/kokoro-wave3/baseline.json`

Expected: PASS. Any failure is a hard stop before Task 1; this plan does not authorize changing approval state or fabricating
dependency evidence.

- [ ] **Step 5: Commit the gate**

```bash
git add -- scripts/wave3/preflight.mjs scripts/wave3/preflight.test.mjs
git commit -m "build(wave3): add dependency and isolation preflight"
```

## Chunk 1: Root contract and Platform Admission

### Task 1: Freeze the Admission command contract

**Repository:** Root

**Files:**
- Modify: `contract/proto/kokoro/platform/admission/v1/admission.proto`
- Modify: `contract/registry/boundaries.yaml`
- Modify: `contract/tests/test_buf_contract.py`
- Modify: `scripts/contract/check-boundary-registry.test.mjs`
- Test: `contract/tests/test_generate.py`

- [ ] **Step 1: Write the failing contract tests**

Assert the service exposes exactly `PrepareRun`, `FinalizeRunAuthorization`, `ReleaseRunAuthorization`,
`ReconcileRunAuthorization`, and `GetCommandReceipt`; every effectful request contains validated `site_id`, command identity,
request digest, and the spec fields. Assert `PrepareRunEffect` has no namespace, capability snapshot, runtime config, Hold, or
Segment supplied by Session. Assert registry remains `contract-only` and provider boundary is `service.platform`.

- [ ] **Step 2: Run the red tests**

Run: `uv run --locked python -m pytest contract/tests/test_buf_contract.py contract/tests/test_generate.py -q && node --test scripts/contract/check-boundary-registry.test.mjs`

Expected: FAIL because v1 still accepts caller namespace/authorization refs and exposes terminal `FinalizeRun` only.

- [ ] **Step 3: Replace the contract cleanly**

Rewrite the contract-only v1 because no active runtime consumer exists. Model accepted/denied/waiting/pending/outcome-unknown
as explicit oneofs; include immutable prepared manifest/runtime/binding/budget refs only in owner responses; add expected Segment
version and evidence refs to finalize/release/reconcile. Keep `GetCommandReceipt` Site/operation/command/digest scoped. Update the
registry operation inventory and receipt/retry metadata without changing lifecycle to active.

- [ ] **Step 4: Generate and verify**

Run: `uv run --locked python -m pytest contract/tests/test_buf_contract.py contract/tests/test_generate.py -q`

Run: `node --test scripts/contract/*.test.mjs && node scripts/contract/check-boundary-registry.mjs`

Expected: PASS; registry reports `platform-admission` as machine-readable and contract-only with five operations.

- [ ] **Step 5: Commit boundary**

```bash
git add -- contract/proto/kokoro/platform/admission/v1/admission.proto contract/registry/boundaries.yaml contract/tests/test_buf_contract.py contract/tests/test_generate.py scripts/contract/check-boundary-registry.test.mjs
git commit -m "feat(contract): freeze run admission authorization commands"
```

### Task 2: Freeze Session HTTP/events and generate all mirrors

**Repository:** Root plus generated files in Platform/Session; no handwritten generated edits

**Files:**
- Modify: `contract/spec/http.yaml`
- Modify: `contract/spec/events.yaml`
- Modify: `contract/buf.gen.yaml`
- Modify: `contract/generate.mjs`
- Modify: `contract/tests/test_generate.py`
- Create: `kokoro-platform/src/interfaces/connect/generated/kokoro/platform/admission/v1/admission_pb.ts`
- Create: `kokoro-session/src/platform/generated/kokoro/platform/admission/v1/admission_pb.ts`
- Replace generated mirror: `kokoro-session/src/contract/http.ts`
- Replace generated mirror: `kokoro-session/src/contract/session-events.ts`
- Create: `kokoro-web/packages/session-client/src/generated/http.ts`
- Create: `kokoro-web/packages/session-client/src/generated/events.ts`
- Create: `kokoro-platform/test/contract/admission-generated.test.ts`
- Create: `kokoro-session/tests/admission-generated.test.ts`
- Modify: `scripts/repository/check-generated-contracts.test.mjs`

- [ ] **Step 1: Add red parity tests**

First assert Root HTTP/events define complete snapshot, typed parts, Branch commands, organization/search, receipt endpoints, opaque
cursor/SSE repair actions, launch/control/cost projection, and no optional messages/seq-0 fallback. Require Admission provider/client
and Session HTTP/event mirrors to carry root digests. Add a negative fixture proving a hand-edited mirror or stale digest fails.

- [ ] **Step 2: Run red tests**

Run: `node --test scripts/repository/check-generated-contracts.test.mjs`

Expected: FAIL because Root still describes the legacy flat Session surface and provider/consumer mirror targets do not exist.

- [ ] **Step 3: Add generator targets and regenerate**

Replace the legacy Session browser contract with the approved breaking shape, then generate Buf ES descriptors plus Session/Web
runtime schemas into target directories. Generated barrels may re-export descriptors; no domain wrapper is generated into Root.
Keep `contract/spec/control.yaml` and the GA generated mirror byte-identical.

- [ ] **Step 4: Verify each repository**

Run: `node scripts/repository/check-generated-contracts.mjs && pnpm -C kokoro-platform exec vitest run test/contract/admission-generated.test.ts`

Run: `npm --prefix kokoro-session exec -- vitest run tests/admission-generated.test.ts tests/contract-gate.test.ts`

Expected: PASS and no generated diff after a second generation run.

- [ ] **Step 5: Commit boundaries**

Commit Root generator changes first, then generated mirrors in their owning subrepositories:

```bash
git add -- contract/spec/http.yaml contract/spec/events.yaml contract/buf.gen.yaml contract/generate.mjs contract/tests/test_generate.py scripts/repository/check-generated-contracts.test.mjs
git commit -m "feat(contract): freeze Session browser and Admission mirrors"
git -C kokoro-platform add -- src/interfaces/connect/generated/kokoro/platform/admission/v1/admission_pb.ts test/contract/admission-generated.test.ts
git -C kokoro-platform commit -m "build: generate admission contract mirror"
git -C kokoro-session add -- src/platform/generated/kokoro/platform/admission/v1/admission_pb.ts src/contract/http.ts src/contract/session-events.ts tests/admission-generated.test.ts
git -C kokoro-session commit -m "build: generate Session and Admission mirrors"
git -C kokoro-web add -- packages/session-client/src/generated/http.ts packages/session-client/src/generated/events.ts
git -C kokoro-web commit -m "build: generate Session browser mirrors"
```

### Task 3: Add Platform Admission persistence and state machines

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/20260728030100_run_admission/migration.sql`
- Create: `kokoro-platform/src/workflows/run-admission/domain.ts`
- Create: `kokoro-platform/src/workflows/run-admission/contracts.ts`
- Create: `kokoro-platform/src/workflows/run-admission/repository.ts`
- Create: `kokoro-platform/src/workflows/run-admission/INDEX.md`
- Create: `kokoro-platform/test/unit/run-admission-state.test.ts`
- Create: `kokoro-platform/test/integration/run-admission-schema.test.ts`

- [ ] **Step 1: Write state and real-PostgreSQL red tests**

Cover receipt same-key/same-digest, different-digest conflict, unique Site/session binding and namespace, one manifest per launch,
immutable W2A Segment refs, legal Admission receipt/manifest transitions, composite Site FKs, and rollback of Admission
receipt/outbox with the effect. Assert the migration creates no Credit, Hold, allocation, or AuthorizationSegment table/state owner.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-platform vitest run test/unit/run-admission-state.test.ts test/integration/run-admission-schema.test.ts`

Expected: FAIL because the tables and state machine do not exist. Missing PostgreSQL is a failure, not a skip.

- [ ] **Step 3: Add the minimum schema and domain**

Add only `admission_command_receipt`, `platform_session_execution_binding`, `execution_manifest`, and
`admission_domain_outbox`, with immutable refs to W2A-owned execution budget root/root Hold/allocation/AuthorizationSegment facts.
Resolve and mutate those facts exclusively through the already-landed typed `RunBudgetAuthority` application port inside the same
Wave 1 `PlatformUnitOfWork`; do not create an Admission-owned Segment table, repository, transition function, balance, or allocation.
Keep request/result digests fixed-length and enforce immutable source identity with unique keys.

- [ ] **Step 4: Verify migration and tests**

Run: `pnpm -C kokoro-platform db:generate && pnpm -C kokoro-platform db:migrate`

Run: `pnpm -C kokoro-platform vitest run test/unit/run-admission-state.test.ts test/integration/run-admission-schema.test.ts`

Expected: PASS including rollback and constraint assertions.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-platform add -- prisma/schema.prisma prisma/migrations/20260728030100_run_admission/migration.sql src/workflows/run-admission/domain.ts src/workflows/run-admission/contracts.ts src/workflows/run-admission/repository.ts src/workflows/run-admission/INDEX.md test/unit/run-admission-state.test.ts test/integration/run-admission-schema.test.ts
git -C kokoro-platform commit -m "feat(admission): add authorization persistence"
```

### Task 4: Implement PrepareRun as one Platform workflow

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/src/workflows/run-admission/resolve-inputs.ts`
- Create: `kokoro-platform/src/workflows/run-admission/prepare-run.ts`
- Create: `kokoro-platform/src/workflows/run-admission/manifest-digest.ts`
- Create: `kokoro-platform/test/unit/prepare-run.test.ts`
- Create: `kokoro-platform/test/integration/prepare-run-postgres.test.ts`

- [ ] **Step 1: Write failing policy and atomicity tests**

Cover invalid SiteAccessGrant, wrong Project/member, revoked capability/model/AssetGrant, stale epoch, insufficient credit, remote
owner outage, first-session binding, replay, digest conflict, and failure injection at manifest/Admission receipt/outbox writes plus
every typed `RunBudgetAuthority` outcome.
Every denial must produce zero executable manifest/Segment/dispatch fact.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-platform vitest run test/unit/prepare-run.test.ts test/integration/prepare-run-postgres.test.ts`

Expected: FAIL with missing `prepareRun` workflow.

- [ ] **Step 3: Implement the minimum workflow**

Resolve signed Capability/Model/Asset owner evidence before opening the database transaction; fail closed on owner timeout. Inside
one `PlatformUnitOfWork`, rebuild `RequestSecurityContext`, recheck local Site/Project/Entitlement/Restriction epochs, create/read
the Session binding and opaque GA namespace, freeze runtime/manifest/rating refs, invoke the W2A typed `RunBudgetAuthority` port to
reserve/read the sole W2A root Hold/allocation/Segment, then persist only returned refs with the Admission receipt/outbox. Never
import Credit infrastructure, write Segment rows directly, or perform a remote call inside the PostgreSQL transaction.

- [ ] **Step 4: Verify focused and Platform suites**

Run: `pnpm -C kokoro-platform vitest run test/unit/prepare-run.test.ts test/integration/prepare-run-postgres.test.ts`

Run: `pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`

Expected: PASS; GA namespace appears only in prepared response/persisted binding, never in request authority.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-platform add -- src/workflows/run-admission/resolve-inputs.ts src/workflows/run-admission/prepare-run.ts src/workflows/run-admission/manifest-digest.ts test/unit/prepare-run.test.ts test/integration/prepare-run-postgres.test.ts
git -C kokoro-platform commit -m "feat(admission): prepare immutable run authorization"
```

### Task 5: Implement Finalize, Release, Reconcile, and receipt recovery

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/src/workflows/run-admission/finalize-authorization.ts`
- Create: `kokoro-platform/src/workflows/run-admission/release-authorization.ts`
- Create: `kokoro-platform/src/workflows/run-admission/reconcile-authorization.ts`
- Create: `kokoro-platform/src/workflows/run-admission/get-command-receipt.ts`
- Create: `kokoro-platform/test/integration/admission-command-recovery.test.ts`
- Create: `kokoro-platform/test/property/authorization-segment.test.ts`

- [ ] **Step 1: Write the crash/CAS red matrix**

Cover every §9.5 crash point: response loss, finalize/cancel race, stale expected version, reserved expiry, committed non-release,
outcome unknown, duplicate owner evidence, and reconciliation to settled. Generate typed legal/illegal command/result sequences
against a `RunBudgetAuthority` contract fake and prove Admission never applies a Segment transition itself.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-platform vitest run test/integration/admission-command-recovery.test.ts test/property/authorization-segment.test.ts`

Expected: FAIL because command handlers are missing.

- [ ] **Step 3: Implement transaction-scoped commands**

Finalize asks `RunBudgetAuthority` to CAS the referenced W2A Segment reserved→committed with prerequisite receipts; Release asks the
same port to release only a reserved slice with trusted no-dispatch evidence; Reconcile passes Session owner-issued dispatch/terminal
receipts derived from the existing GA event stream and never trusts caller absence claims. Admission persists the returned W2A refs,
versions, owner receipts and its own outbox atomically, but owns no Segment transition code or table. It does not call a new GA
receipt/lookup API or require a GA wire change. Receipt lookup is Site/operation/command/digest scoped and cross-Site non-disclosing.

- [ ] **Step 4: Verify**

Run: `pnpm -C kokoro-platform vitest run test/integration/admission-command-recovery.test.ts test/property/authorization-segment.test.ts`

Expected: PASS with committed Segments never released by TTL or rollback helpers.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-platform add -- src/workflows/run-admission/finalize-authorization.ts src/workflows/run-admission/release-authorization.ts src/workflows/run-admission/reconcile-authorization.ts src/workflows/run-admission/get-command-receipt.ts test/integration/admission-command-recovery.test.ts test/property/authorization-segment.test.ts
git -C kokoro-platform commit -m "feat(admission): finalize and reconcile authorization"
```

### Task 6: Expose the Connect provider and durable worker

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/src/interfaces/connect/admission/service.ts`
- Create: `kokoro-platform/src/interfaces/connect/admission/router.ts`
- Create: `kokoro-platform/src/interfaces/connect/admission/workload-auth.ts`
- Modify: `kokoro-platform/src/process/api.ts`
- Modify: `kokoro-platform/src/process/worker.ts`
- Create: `kokoro-platform/test/integration/admission-connect.test.ts`
- Create: `kokoro-platform/test/integration/admission-outbox-worker.test.ts`

- [ ] **Step 1: Write red transport/security tests**

Use a real Connect client. Reject missing/wrong audience, body Site mismatch, oversized/unknown payload, invalid digest, stale
workload grant, and cross-Site receipt lookup. Inject relay crash after publish and prove identical aggregate-version replay.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-platform vitest run test/integration/admission-connect.test.ts test/integration/admission-outbox-worker.test.ts`

Expected: FAIL because the provider route and worker are not registered.

- [ ] **Step 3: Wire generated descriptors to workflows**

Use existing Platform Connect interceptors and workload exchange; do not add a second auth secret scheme. Register API health/readiness
only after PostgreSQL, contract revision, verifier keys, and workflow ports are ready. Worker uses `FOR UPDATE SKIP LOCKED`, leases,
attempt caps, and dead/reconcile state.

- [ ] **Step 4: Run full Platform verification**

Run: `pnpm -C kokoro-platform test && pnpm -C kokoro-platform test:integration && pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`

Expected: all PASS.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-platform add -- src/interfaces/connect/admission/service.ts src/interfaces/connect/admission/router.ts src/interfaces/connect/admission/workload-auth.ts src/process/api.ts src/process/worker.ts test/integration/admission-connect.test.ts test/integration/admission-outbox-worker.test.ts
git -C kokoro-platform commit -m "feat(admission): serve production Connect workflow"
```

**Chunk 1 GA gate:** the Root integrator runs
`node scripts/wave3/preflight.mjs --verify-baseline .git/kokoro-wave3/baseline.json --ga-only`; it must compare Agent SHA/full
porcelain status, both control hashes, and both canonical `run.request`/`run.cancel` golden-byte hashes. Any drift blocks Chunk 2.

## Chunk 2: Session PostgreSQL, launch, projection, and transport

### Task 7: Install the Session PostgreSQL persistence baseline

**Repository:** `kokoro-session`

**Files:**
- Modify: `kokoro-session/package.json`
- Modify: `kokoro-session/package-lock.json`
- Create: `kokoro-session/prisma.config.ts`
- Create: `kokoro-session/prisma/schema.prisma`
- Create: `kokoro-session/prisma/migrations/20260728030200_session_projection/migration.sql`
- Create: `kokoro-session/src/store/postgres/client.ts`
- Create: `kokoro-session/src/store/postgres/transaction.ts`
- Create: `kokoro-session/tests/postgres-schema.test.ts`
- Create: `kokoro-session/tests/postgres-rls.test.ts`

- [ ] **Step 1: Write real-PostgreSQL red tests**

Assert composite Site keys/FKs, Branch empty/non-empty constraints, immutable message ordinals, one launch/run, Inbox digest conflict,
DLQ uniqueness, receipt digest, RLS Site/subject generation isolation, and application role without `BYPASSRLS`.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run postgres-schema.test.ts postgres-rls.test.ts`

Expected: FAIL because Session has no PostgreSQL schema/client. Missing default PostgreSQL is a hard failure.

- [ ] **Step 3: Add Prisma 7 schema and explicit SQL policies**

Implement §5 tables, partial/deferrable constraints and RLS in migration SQL. Use `DATABASE_URL_SESSION`; migrations run only from
the one-shot migrator, never API startup. Add transaction helper that sets verified `app.site_id`, `app.subject_ref`, and
`app.subject_generation` locally for each transaction.

- [ ] **Step 4: Verify**

Run: `npm --prefix kokoro-session run db:generate && npm --prefix kokoro-session run db:migrate:test`

Run: `npm --prefix kokoro-session test -- --run postgres-schema.test.ts postgres-rls.test.ts`

Expected: PASS and test schema/database cleanup completes.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-session add -- package.json package-lock.json prisma.config.ts prisma/schema.prisma prisma/migrations/20260728030200_session_projection/migration.sql src/store/postgres/client.ts src/store/postgres/transaction.ts tests/postgres-schema.test.ts tests/postgres-rls.test.ts
git -C kokoro-session commit -m "feat(store): add PostgreSQL session projection schema"
```

### Task 8: Implement empty Session and immutable conversation commands

**Repository:** `kokoro-session`

**Files:**
- Create: `kokoro-session/src/conversation/contracts.ts`
- Create: `kokoro-session/src/conversation/create-session.ts`
- Create: `kokoro-session/src/conversation/submit-message.ts`
- Create: `kokoro-session/src/conversation/repository.ts`
- Create: `kokoro-session/src/conversation/INDEX.md`
- Create: `kokoro-session/tests/conversation-create.test.ts`
- Create: `kokoro-session/tests/conversation-submit.test.ts`

- [ ] **Step 1: Write red command tests**

Prove CreateSession writes only empty initial Branch/receipt/event; replay returns the same object; first Submit atomically writes user
parts, assistant placeholder, Branch roots/leaves, launch, receipt, events, and PREPARE outbox. Inject failure at every write and
expect zero partial rows. Active Run returns `ACTIVE_RUN_EXISTS`, never `run.steer`.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run conversation-create.test.ts conversation-submit.test.ts`

Expected: FAIL with missing commands.

- [ ] **Step 3: Implement minimum commands**

Validate boundary payloads with Zod 4-derived types, expected Session version, Branch parent, ordered typed parts, attachment refs,
and ModelOptionRevisionRef. Store immutable command receipt and outbox in the same transaction. Do not resolve namespace,
capabilities, model provider, billing, or GA here.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix kokoro-session test -- --run conversation-create.test.ts conversation-submit.test.ts`

```bash
git -C kokoro-session add -- src/conversation/contracts.ts src/conversation/create-session.ts src/conversation/submit-message.ts src/conversation/repository.ts src/conversation/INDEX.md tests/conversation-create.test.ts tests/conversation-submit.test.ts
git -C kokoro-session commit -m "feat(conversation): persist empty sessions and message intents"
```

### Task 9: Add the Admission client and command outbox scanner

**Repository:** `kokoro-session`

**Files:**
- Modify: `kokoro-session/package.json`
- Modify: `kokoro-session/package-lock.json`
- Replace: `kokoro-session/src/platform/admission-port.ts`
- Create: `kokoro-session/src/platform/connect-admission-client.ts`
- Create: `kokoro-session/src/platform/admission-outbox-scanner.ts`
- Create: `kokoro-session/src/platform/admission-reconciler.ts`
- Modify: `kokoro-session/src/platform/INDEX.md`
- Create: `kokoro-session/tests/platform-admission-client.test.ts`
- Create: `kokoro-session/tests/platform-admission-outbox.test.ts`

- [ ] **Step 1: Write red client/recovery tests**

Use a local Connect fake to cover deadline, same command replay, receipt pending/not-found, different digest conflict, response loss,
and Site/workload binding. Prove PREPARE result + FINALIZE outbox and FINALIZE receipt + dispatch outbox are each atomic Session
transactions. No test may use legacy billing/Hub/model methods.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run platform-admission-client.test.ts platform-admission-outbox.test.ts`

Expected: FAIL because the port still exposes legacy namespace/billing methods.

- [ ] **Step 3: Implement generated Connect client and scanners**

Add exact Connect 2.1.2 dependencies. Send only contract request fields, persist returned binding/runtime/namespace ciphertext and
safe display snapshot, and query the same receipt after ambiguous outcomes. Scanner uses lease/attempt/dead state; dead rows remain
reconciliation-owned, not business-failed.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix kokoro-session test -- --run platform-admission-client.test.ts platform-admission-outbox.test.ts && npm --prefix kokoro-session run typecheck`

```bash
git -C kokoro-session add -- package.json package-lock.json src/platform/admission-port.ts src/platform/connect-admission-client.ts src/platform/admission-outbox-scanner.ts src/platform/admission-reconciler.ts src/platform/INDEX.md tests/platform-admission-client.test.ts tests/platform-admission-outbox.test.ts
git -C kokoro-session commit -m "feat(admission): consume durable Platform authorization"
```

### Task 10: Fence GA dispatch and cancellation without changing wire

**Repository:** `kokoro-session`

**Files:**
- Create: `kokoro-session/src/relay/run-dispatch-outbox.ts`
- Rewrite: `kokoro-session/src/relay/control-outbox-scanner.ts`
- Rewrite: `kokoro-session/src/relay/control.ts`
- Create: `kokoro-session/tests/run-dispatch-outbox.test.ts`
- Rewrite: `kokoro-session/tests/control-outbox.test.ts`
- Modify: `kokoro-session/tests/contract-gate.test.ts`

- [ ] **Step 1: Write red byte-parity and crash tests**

Assert dispatch is impossible before a committed finalize receipt; repeated XADD uses identical existing `run.request` bytes;
same run/different digest is rejected; XADD/receipt crash becomes `dispatch_unknown`; pre-dispatch cancel races Finalize by version;
post-observation cancel sends the existing `run.cancel` only. Assert no authorization field enters GA wire.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run run-dispatch-outbox.test.ts control-outbox.test.ts contract-gate.test.ts`

Expected: FAIL against direct/legacy dispatch.

- [ ] **Step 3: Implement fenced outboxes**

Build immutable GA payload once from the Platform-prepared runtime and Session trigger, hash it, and CAS the local launch fence plus
stored committed receipt before publish. First durable GA event—not XADD—marks event observed. Keep control decision identity and
expected RunView version local; existing GA control envelope stays unchanged.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix kokoro-session test -- --run run-dispatch-outbox.test.ts control-outbox.test.ts contract-gate.test.ts`

```bash
git -C kokoro-session add -- src/relay/run-dispatch-outbox.ts src/relay/control-outbox-scanner.ts src/relay/control.ts tests/run-dispatch-outbox.test.ts tests/control-outbox.test.ts tests/contract-gate.test.ts
git -C kokoro-session commit -m "feat(relay): fence dispatch on committed authorization"
```

### Task 10A: Verify SessionAccessGrant and maintain the local revocation projection

**Repository:** `kokoro-session`

**Files:**
- Create: `kokoro-session/src/browser/access-grant.ts`
- Create: `kokoro-session/src/browser/workload-authenticator.ts`
- Create: `kokoro-session/src/authorization/platform-authorization-consumer.ts`
- Create: `kokoro-session/src/store/postgres/platform-authorization-projection.ts`
- Create: `kokoro-session/prisma/migrations/20260728_platform_authorization_projection/migration.sql`
- Modify: `kokoro-session/src/store/postgres/transaction.ts`
- Modify: `kokoro-session/src/main.ts`
- Create: `kokoro-session/tests/session-access-grant.test.ts`
- Create: `kokoro-session/tests/platform-authorization-projection.test.ts`

- [ ] Reject production startup without a dedicated Platform Authorization issuer/JWKS or pinned verifier key, an independent BFF
  workload authenticator, and the compatible authorization-feed consumer. Do not accept the legacy general Auth JWT as a
  SessionAccessGrant and do not provide browser CORS on the v3 server-to-server entry.
- [ ] Verify `alg=RS256`, exact issuer/audience/kid/jti/iat/nbf/exp, five-minute maximum lifetime, the full positive-uint64 epoch
  vector, and the explicit project/session/run resource union. Cross-bind the trusted workload claims and grant across
  SiteProjectBinding/deployment/Site/release/artifact/environment/region/contract revision; mismatch is non-disclosing.
- [ ] Consume signed Platform authorization events through inbox+digest dedupe and monotonic cursor/aggregate revocation epoch.
  A signed grant may seed a missing projection but may never overwrite a higher epoch. Signature failure, cursor gap, epoch rollback,
  unknown key, or projection freshness older than 30 seconds makes authorization unavailable/fail-closed until snapshot/replay heals.
- [ ] Require both Platform authorization projection and Session-owned `session_access_acl_projection` for every read, mutation,
  control, snapshot and SSE connection. Recheck on SSE heartbeat no slower than 15 seconds; do not make a synchronous Platform call
  on every HTTP/SSE hot-path operation.
- [ ] Prove Site suspend, session revoke, membership remove, subject generation and every security epoch closes existing SSE and
  rejects old reads/controls within the revocation budget. Prove BFF workload failure has distinct
  `BFF_WORKLOAD_REQUIRED|BFF_WORKLOAD_REVOKED` safe errors rather than masquerading as user grant failure.
- [ ] Run focused security/projection suites, lint and typecheck, then commit this slice before Task 11 exposes the complete reader.

### Task 11: Build Inbox, projection, complete snapshot, and opaque SSE

**Repository:** `kokoro-session`

**Files:**
- Create: `kokoro-session/src/projection/agent-event-inbox.ts`
- Create: `kokoro-session/src/projection/session-projector.ts`
- Create: `kokoro-session/src/projection/snapshot-query.ts`
- Create: `kokoro-session/src/projection/dlq.ts`
- Create: `kokoro-session/src/http/cursor.ts`
- Rewrite: `kokoro-session/src/http/sse.ts`
- Modify: `kokoro-session/src/http/server.ts`
- Create: `kokoro-session/tests/projection-inbox.test.ts`
- Create: `kokoro-session/tests/snapshot-consistency.test.ts`
- Rewrite: `kokoro-session/tests/sse.test.ts`

- [ ] **Step 1: Write red projection/transport tests**

Cover duplicate event, same ID/different digest DLQ, gap without checkpoint advance, unknown part→unsupported, malformed known frame
repair, snapshot transaction watermark, active Branch completeness, signed cursor tamper/ahead/epoch/subject/Site/schema errors,
15s jitter heartbeat, buffer cap, slow consumer drain, attach race, and no seq-0 fallback.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run projection-inbox.test.ts snapshot-consistency.test.ts sse.test.ts`

Expected: FAIL because current snapshot omits messages and SSE accepts numeric fallback.

- [ ] **Step 3: Implement authority-preserving projection**

Persist Inbox and projection/checkpoint in one PostgreSQL transaction. Quarantine malformed durable events without advancing past the
gap. Query snapshot from one projection boundary. Sign opaque cursor with Site/session/subject-generation/audience/epoch/revision;
return typed repair actions. Live deltas remain connection-local and never become durable cursor truth.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix kokoro-session test -- --run projection-inbox.test.ts snapshot-consistency.test.ts sse.test.ts`

```bash
git -C kokoro-session add -- src/projection/agent-event-inbox.ts src/projection/session-projector.ts src/projection/snapshot-query.ts src/projection/dlq.ts src/http/cursor.ts src/http/sse.ts src/http/server.ts tests/projection-inbox.test.ts tests/snapshot-consistency.test.ts tests/sse.test.ts
git -C kokoro-session commit -m "feat(projection): serve complete snapshots and resumable SSE"
```

### Task 12: Add Branch, organization, and reliable command APIs

**Repository:** `kokoro-session`

**Files:**
- Create: `kokoro-session/src/conversation/branch-commands.ts`
- Create: `kokoro-session/src/conversation/organization.ts`
- Create: `kokoro-session/src/conversation/search.ts`
- Modify: `kokoro-session/src/http/server.ts`
- Create: `kokoro-session/tests/branch-commands.test.ts`
- Create: `kokoro-session/tests/session-organization.test.ts`
- Create: `kokoro-session/tests/session-search.test.ts`

- [ ] **Step 1: Write red command tests**

Cover edit/regenerate/fork/activate provenance without old-row mutation, stable list/search cursor, safe-text-only indexing,
actor-scoped pin/folder, archive/restore/trash, active Run trash policy, expected-version conflict, replay, and cross-Site/Project denial.

- [ ] **Step 2: Run red tests**

Run: `npm --prefix kokoro-session test -- --run branch-commands.test.ts session-organization.test.ts session-search.test.ts`

Expected: FAIL because server-side Branch and organization commands are absent.

- [ ] **Step 3: Implement minimum APIs**

Use the shared conversation transaction/repository; every command writes receipt and event atomically. Index only title and safe
user/assistant text. Regenerate creates a new launch/Run; transport retry never does. Trash requires cancellation receipt policy.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix kokoro-session test -- --run branch-commands.test.ts session-organization.test.ts session-search.test.ts`

```bash
git -C kokoro-session add -- src/conversation/branch-commands.ts src/conversation/organization.ts src/conversation/search.ts src/http/server.ts tests/branch-commands.test.ts tests/session-organization.test.ts tests/session-search.test.ts
git -C kokoro-session commit -m "feat(conversation): add branches and server organization"
```

### Task 13: Migrate Session data, cut over atomically, and remove legacy production paths

**Repository:** `kokoro-session`

**Files:**
- Modify: `kokoro-session/package.json`
- Modify: `kokoro-session/package-lock.json`
- Delete: `kokoro-session/src/billing/INDEX.md`
- Delete: `kokoro-session/src/billing/client.ts`
- Delete: `kokoro-session/src/billing/config.ts`
- Delete: `kokoro-session/src/billing/reconciler.ts`
- Delete: `kokoro-session/src/billing/service.ts`
- Delete: `kokoro-session/src/hub/resolver.ts`
- Delete: `kokoro-session/src/namespace/profile.ts`
- Delete: `kokoro-session/src/namespace/resolve.ts`
- Delete: `kokoro-session/src/platform/legacy-admission-adapter.ts`
- Delete: `kokoro-session/src/platform/legacy-terminal-event-adapter.ts`
- Remove production assembly: `kokoro-session/src/store/mongo.ts`
- Create: `kokoro-session/src/migration/wave3/preflight.ts`
- Create: `kokoro-session/src/migration/wave3/convert-session.ts`
- Create: `kokoro-session/src/migration/wave3/quarantine.ts`
- Create: `kokoro-session/src/migration/wave3/projection-digest.ts`
- Create: `kokoro-session/src/migration/wave3/cutover.ts`
- Create: `kokoro-session/src/migration/wave3/rollback-evidence.ts`
- Create: `kokoro-session/src/migration/wave3/main.ts`
- Modify: `kokoro-session/src/main.ts`
- Modify: `kokoro-session/src/store/factory.ts`
- Modify: `kokoro-session/tests/repository-boundary.test.ts`
- Create: `kokoro-session/tests/legacy-surface-removed.test.ts`
- Create: `kokoro-session/tests/wave3-migration-preflight.test.ts`
- Create: `kokoro-session/tests/wave3-migration-conversion.test.ts`
- Create: `kokoro-session/tests/wave3-migration-cutover.test.ts`
- Create generated sanitized evidence: `kokoro-session/test/reports/wave3-migration/preflight.json`
- Create generated sanitized evidence: `kokoro-session/test/reports/wave3-migration/conversion.json`
- Create generated sanitized evidence: `kokoro-session/test/reports/wave3-migration/shadow-compare.json`
- Create generated sanitized evidence: `kokoro-session/test/reports/wave3-migration/cutover.json`
- Create generated sanitized evidence: `kokoro-session/test/reports/wave3-migration/rollback.json`

- [ ] **Step 1: Add red negative architecture tests**

Add migration tests requiring an immutable source inventory; frozen old writes; zero active Run, pending pause/control, and billing
reconciliation before conversion; deterministic old Session→original Branch/ordered Message/`text@v1` MessagePart conversion;
read-only treatment for unresolved capability/raw-model history; quarantine rather than guessing ambiguous order/ownership; exact
row/Branch DAG/part/projection/watermark/owner-scope/search digest shadow comparison; one CAS traffic cutover; and rollback evidence
that never restores Mongo writes after PostgreSQL accepts new facts. Also scan production sources/env/routes for billing, Hub
resolution, namespace=owner, raw model provider, Mongo production factory, `GET /billing`, numeric cursor, legacy admission symbols,
and `run.steer` from SubmitMessage.

- [ ] **Step 2: Run red test**

Run: `npm --prefix kokoro-session test -- --run wave3-migration-preflight.test.ts wave3-migration-conversion.test.ts wave3-migration-cutover.test.ts legacy-surface-removed.test.ts repository-boundary.test.ts`

Expected: FAIL because the migration/cutover command and legacy-removal boundary do not exist.

- [ ] **Step 3: Implement conversion, prove shadow parity, cut over, then delete legacy assembly**

Implement a non-production migration command that: records the Mongo source inventory/digest; freezes writes and drains all active or
unresolved work; converts deterministically into PostgreSQL; quarantines unprovable records; rebuilds and shadow-compares the complete
projection; writes signed preflight/conversion/comparison receipts; and CASes one runtime configuration revision to PostgreSQL only
after every count/digest/scope gate passes. Rehearse pre-cutover rollback and post-cutover forward-fix behavior, recording sanitized
rollback evidence. Only after the cutover receipt exists may production Mongo/commercial adapters be removed. Keep audit export/
migration readers reachable only from this explicit command. Production starts only with PostgreSQL, SessionAccessGrant verifier,
Platform Admission client, Redis transport, and compatible contract revision.

- [ ] **Step 4: Run full Session verification**

Run: `npm --prefix kokoro-session run migrate:wave3 -- --dry-run --output test/reports/wave3-migration && npm --prefix kokoro-session run migrate:wave3 -- --verify-shadow --output test/reports/wave3-migration`

Run: `npm --prefix kokoro-session audit --audit-level=high && npm --prefix kokoro-session run lint && npm --prefix kokoro-session run typecheck && npm --prefix kokoro-session test`

Expected: all PASS with no skipped PostgreSQL tests; all five sanitized migration reports validate, and Mongo remains read-only before
the cutover receipt and unreachable from production afterward.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-session add -- package.json package-lock.json src/billing/INDEX.md src/billing/client.ts src/billing/config.ts src/billing/reconciler.ts src/billing/service.ts src/hub/resolver.ts src/namespace/profile.ts src/namespace/resolve.ts src/platform/legacy-admission-adapter.ts src/platform/legacy-terminal-event-adapter.ts src/store/mongo.ts src/migration/wave3/preflight.ts src/migration/wave3/convert-session.ts src/migration/wave3/quarantine.ts src/migration/wave3/projection-digest.ts src/migration/wave3/cutover.ts src/migration/wave3/rollback-evidence.ts src/migration/wave3/main.ts src/main.ts src/store/factory.ts tests/repository-boundary.test.ts tests/legacy-surface-removed.test.ts tests/wave3-migration-preflight.test.ts tests/wave3-migration-conversion.test.ts tests/wave3-migration-cutover.test.ts test/reports/wave3-migration/preflight.json test/reports/wave3-migration/conversion.json test/reports/wave3-migration/shadow-compare.json test/reports/wave3-migration/cutover.json test/reports/wave3-migration/rollback.json
git -C kokoro-session commit -m "refactor(session): migrate and cut over PostgreSQL runtime"
```

**Chunk 2 GA gate:** rerun the same baseline command and require all six GA identity/hash facts plus clean status to match before
starting Web work. Session byte-parity tests supplement this gate; they do not replace the Root baseline comparison.

## Chunk 3: Web shared packages, independent Site fixtures, and promotion

### Task 14: Publish the brandless Session client package

**Repository:** `kokoro-web`

**Files:**
- Modify: `kokoro-web/pnpm-lock.yaml`
- Create: `kokoro-web/packages/session-client/package.json`
- Create: `kokoro-web/packages/session-client/src/client.ts`
- Create: `kokoro-web/packages/session-client/src/contracts.ts`
- Create: `kokoro-web/packages/session-client/src/cursor-policy.ts`
- Create: `kokoro-web/packages/session-client/src/index.ts`
- Create: `kokoro-web/packages/session-client/INDEX.md`
- Create: `kokoro-web/packages/session-client/test/client.test.ts`
- Create: `kokoro-web/packages/session-client/test/cursor-policy.test.ts`

- [ ] **Step 1: Write red client tests**

First create the minimal `package.json` with a failing `test` script target and the test files, but no client implementation; this
ensures the package filter matches during red. Mock HTTP/SSE only at the wire boundary. Prove snapshot-first hydration, cursor error
actions, Last-Event-ID/query conflict, typed parts, command idempotency, typed auth-required propagation, and no seq-0/full-history
request. Token acquisition/refresh is outside this package and is tested only in Task 16.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-web --filter @kokoro/session-client --fail-if-no-match test`

Expected: the package filter MATCHES the scaffold and the test FAILS on a named missing client implementation/export behavior.
`--fail-if-no-match` or package discovery failure is test-infrastructure failure and is not an acceptable RED.

- [ ] **Step 3: Implement generated-contract client**

Consume generated Session HTTP/event schemas, expose narrow query/command/stream interfaces, and keep auth token acquisition outside
the package. Do not depend on Next.js, brand assets, Assistant UI, or Site IDs.

- [ ] **Step 4: Verify and commit**

Run: `pnpm -C kokoro-web --filter @kokoro/session-client --fail-if-no-match test && pnpm -C kokoro-web --filter @kokoro/session-client --fail-if-no-match typecheck`

```bash
git -C kokoro-web add -- pnpm-lock.yaml packages/session-client/package.json packages/session-client/src/client.ts packages/session-client/src/contracts.ts packages/session-client/src/cursor-policy.ts packages/session-client/src/index.ts packages/session-client/INDEX.md packages/session-client/test/client.test.ts packages/session-client/test/cursor-policy.test.ts
git -C kokoro-web commit -m "feat(web): add brandless Session client"
```

### Task 15: Build Chat projection and assistant-ui adapter

**Repository:** `kokoro-web`

**Files:**
- Modify: `kokoro-web/pnpm-lock.yaml`
- Create: `kokoro-web/packages/chat-surface/package.json`
- Create: `kokoro-web/packages/chat-surface/src/projection/store.ts`
- Create: `kokoro-web/packages/chat-surface/src/runtime/kokoro-external-store-adapter.ts`
- Create: `kokoro-web/packages/chat-surface/src/renderers/registry.tsx`
- Create: `kokoro-web/packages/chat-surface/src/components/chat-surface.tsx`
- Create: `kokoro-web/packages/chat-surface/src/index.ts`
- Create: `kokoro-web/packages/chat-surface/INDEX.md`
- Create: `kokoro-web/packages/chat-surface/test/runtime-adapter.test.tsx`
- Create: `kokoro-web/packages/chat-surface/test/projection.test.ts`

- [ ] **Step 1: Add exact dependency and red adapter tests**

First create the minimal package manifest/test scaffold with no runtime adapter so the red command cannot false-green; pin
`@assistant-ui/react` to exactly `0.14.28` and assert lock integrity. Test that `onNew/onEdit/onReload/onCancel` invoke exactly
one Kokoro command, UI completion does not imply Run terminal, unknown parts render unsupported, branch/cancelling comes only from
Kokoro projection, and snapshot rehydrate replaces—not duplicates—history.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-web --filter @kokoro/chat-surface --fail-if-no-match test`

Expected: the package filter MATCHES the scaffold and the test FAILS on a named missing adapter/export behavior. Package no-match
is test-infrastructure failure, not feature RED.

- [ ] **Step 3: Implement the ExternalStoreRuntime adapter**

Use `useExternalStoreRuntime`; map complete snapshot plus durable/live deltas into Assistant UI messages without adopting
AssistantCloud, AssistantTransport, AI SDK transport, or `thread.export()` persistence. Route typed parts through Kokoro renderers;
keep approval/HITL owner receipts intact.

- [ ] **Step 4: Verify and commit**

Run: `pnpm -C kokoro-web --filter @kokoro/chat-surface --fail-if-no-match test && pnpm -C kokoro-web --filter @kokoro/chat-surface --fail-if-no-match typecheck`

```bash
git -C kokoro-web add -- pnpm-lock.yaml packages/chat-surface/package.json packages/chat-surface/src/projection/store.ts packages/chat-surface/src/runtime/kokoro-external-store-adapter.ts packages/chat-surface/src/renderers/registry.tsx packages/chat-surface/src/components/chat-surface.tsx packages/chat-surface/src/index.ts packages/chat-surface/INDEX.md packages/chat-surface/test/runtime-adapter.test.tsx packages/chat-surface/test/projection.test.ts
git -C kokoro-web commit -m "feat(web): adapt Chat projection to assistant-ui"
```

### Task 16: Add fail-closed BFF runtime and Site bootstrap

**Repository:** `kokoro-web`

**Files:**
- Modify: `kokoro-web/pnpm-lock.yaml`
- Create: `kokoro-web/packages/bff-runtime/package.json`
- Create: `kokoro-web/packages/bff-runtime/src/site-binding.ts`
- Create: `kokoro-web/packages/bff-runtime/src/session-access.ts`
- Create: `kokoro-web/packages/bff-runtime/src/session-proxy.ts`
- Create: `kokoro-web/packages/bff-runtime/src/index.ts`
- Create: `kokoro-web/packages/bff-runtime/INDEX.md`
- Create: `kokoro-web/packages/bff-runtime/test/site-binding.test.ts`
- Create: `kokoro-web/packages/bff-runtime/test/session-proxy.test.ts`

- [ ] **Step 1: Write red security tests**

First create the minimal package manifest/test scaffold without BFF implementation so the filter is guaranteed to match and fail.
Reject missing/revoked workload binding, wrong artifact digest, stale SiteRelease/subject generation, browser siteId/namespace/raw
Bearer, wrong Session audience, production unsafe fallback, and cross-Site response. Assert purpose-specific short grants are
acquired/refreshed server-side here, never by `session-client`.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-web --filter @kokoro/bff-runtime --fail-if-no-match test`

Expected: the package filter MATCHES the scaffold and the test FAILS on a named missing BFF security/refresh/export behavior.
Package no-match is test-infrastructure failure and cannot satisfy RED.

- [ ] **Step 3: Implement workload exchange and proxy helpers**

Take deployment binding from server-only configuration, exchange it with Platform, verify artifact digest, combine AuthSession actor,
request a purpose-specific SessionAccessGrant, and proxy without accepting authority fields from the browser. Local unsafe mode is
explicitly watermarked and rejected by production build validation.

- [ ] **Step 4: Verify and commit**

Run: `pnpm -C kokoro-web --filter @kokoro/bff-runtime --fail-if-no-match test && pnpm -C kokoro-web --filter @kokoro/bff-runtime --fail-if-no-match typecheck`

```bash
git -C kokoro-web add -- pnpm-lock.yaml packages/bff-runtime/package.json packages/bff-runtime/src/site-binding.ts packages/bff-runtime/src/session-access.ts packages/bff-runtime/src/session-proxy.ts packages/bff-runtime/src/index.ts packages/bff-runtime/INDEX.md packages/bff-runtime/test/site-binding.test.ts packages/bff-runtime/test/session-proxy.test.ts
git -C kokoro-web commit -m "feat(web): add fail-closed Site BFF runtime"
```

### Task 17: Convert `apps/user` into the reference Site harness

**Repository:** `kokoro-web`

**Files:**
- Modify: `kokoro-web/pnpm-lock.yaml`
- Modify: `kokoro-web/apps/user/package.json`
- Rewrite: `kokoro-web/apps/user/src/app/page.tsx`
- Rewrite: `kokoro-web/apps/user/src/app/api/session/[...path]/route.ts`
- Rewrite: `kokoro-web/apps/user/src/lib/server/site.ts`
- Rewrite: `kokoro-web/apps/user/src/lib/server/auth.ts`
- Replace: `kokoro-web/apps/user/src/core/hydration.ts`
- Replace: `kokoro-web/apps/user/src/core/projections.ts`
- Replace: `kokoro-web/apps/user/src/core/reducer.ts`
- Replace: `kokoro-web/apps/user/src/core/state.ts`
- Replace: `kokoro-web/apps/user/src/engine/client.ts`
- Replace: `kokoro-web/apps/user/src/engine/machine.ts`
- Replace: `kokoro-web/apps/user/src/engine/reattach.ts`
- Replace: `kokoro-web/apps/user/src/engine/use-session-engine.ts`
- Modify: `kokoro-web/test/repository/ci-workflow.test.mjs`
- Create: `kokoro-web/test/repository/reference-app-not-production.test.mjs`
- Create: `kokoro-web/apps/user/tests/e2e/chat-reference.spec.ts`

- [ ] **Step 1: Write red repository/UI tests**

Require `apps/user` production deploy to fail, shared packages to provide Chat behavior, complete snapshot hydration, reliable Stop,
branch/search/org flows, no Host/default Site fallback, no direct Session Bearer, and Wave 4 off hiding Studio/Library/upload.

- [ ] **Step 2: Run red tests**

Run: `pnpm -C kokoro-web test:repository && pnpm -C kokoro-web --filter @kokoro/web-user test`

Expected: FAIL against the current universal runtime skin and legacy billing/Hub/artifact surfaces.

- [ ] **Step 3: Rebuild as a scaffold/reference harness**

Compose `session-client`, `chat-surface`, `bff-runtime`, design-system/i18n; keep sample branding local. Delete runtime Host skinning,
billing checkout/mock pay, Team shortcut, direct Hub/session proxy, flat reducer, seq-0 reconnect, and Studio naming. Add an explicit
repository gate that prevents this reference app from being promoted as a production Site artifact.

- [ ] **Step 4: Verify and commit**

Run: `pnpm -C kokoro-web test && pnpm -C kokoro-web typecheck && pnpm -C kokoro-web lint && pnpm -C kokoro-web --filter @kokoro/web-user build`

```bash
git -C kokoro-web add -- pnpm-lock.yaml apps/user/package.json apps/user/src/app/page.tsx 'apps/user/src/app/api/session/[...path]/route.ts' apps/user/src/lib/server/site.ts apps/user/src/lib/server/auth.ts apps/user/src/core/hydration.ts apps/user/src/core/projections.ts apps/user/src/core/reducer.ts apps/user/src/core/state.ts apps/user/src/engine/client.ts apps/user/src/engine/machine.ts apps/user/src/engine/reattach.ts apps/user/src/engine/use-session-engine.ts test/repository/ci-workflow.test.mjs test/repository/reference-app-not-production.test.mjs apps/user/tests/e2e/chat-reference.spec.ts
git -C kokoro-web commit -m "refactor(web): make user app a reference Site harness"
```

### Task 18: Prove two independent external Site repositories

**Repository:** `kokoro-web`; generated repositories live in temporary directories outside the workspace

**Files:**
- Modify: `kokoro-web/pnpm-lock.yaml`
- Create: `kokoro-web/packages/site-scaffold/package.json`
- Create: `kokoro-web/packages/site-scaffold/src/create-site-project.ts`
- Create: `kokoro-web/packages/site-scaffold/templates/site/package.json`
- Create: `kokoro-web/packages/site-scaffold/templates/site/next.config.ts`
- Create: `kokoro-web/packages/site-scaffold/templates/site/tsconfig.json`
- Create: `kokoro-web/packages/site-scaffold/templates/site/.github/workflows/site-ci.yml`
- Create: `kokoro-web/packages/site-scaffold/templates/site/public/icon.svg`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/globals.css`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/layout.tsx`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/page.tsx`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/api/session/[...path]/route.ts`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/privacy/page.tsx`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/app/terms/page.tsx`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/analytics.ts`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/brand/tokens.css`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/i18n/en.json`
- Create: `kokoro-web/packages/site-scaffold/templates/site/src/lib/site-manifest.ts`
- Create: `kokoro-web/packages/site-scaffold/INDEX.md`
- Create: `kokoro-web/test/fixtures/external-sites/site-alpha.json`
- Create: `kokoro-web/test/fixtures/external-sites/site-beta.json`
- Create: `kokoro-web/test/repository/external-site-artifacts.test.mjs`
- Create: `kokoro-web/apps/user/tests/e2e/external-site-isolation.spec.ts`
- Create: `kokoro-web/scripts/certify-external-sites.mjs`
- Create generated sanitized evidence: `kokoro-web/test/reports/external-sites/site-alpha.json`
- Create generated sanitized evidence: `kokoro-web/test/reports/external-sites/site-beta.json`
- Create generated sanitized evidence: `kokoro-web/test/reports/external-sites/summary.json`

- [ ] **Step 1: Write the red independence test**

Test one orchestrator contract that packs exact shared package versions, generates Site Alpha and Beta into two OS temp roots,
initializes separate Git repositories, and requires an independent CI config, package.json, frozen lock, commit, artifact,
brand/legal/route/binding digest for each. It must clean-install/build both, start distinct deployments, activate each binding through
the real local Platform contract, run cross-Site/Host/cookie isolation, independently roll back Alpha then Beta, and prove the other
deployment is unchanged. Reject workspace/sibling imports and `if(siteId)`; redact temp paths, credentials and user data from output.

- [ ] **Step 2: Run red test**

Run: `node --test kokoro-web/test/repository/external-site-artifacts.test.mjs`

Expected: FAIL because no scaffold or independent artifacts exist.

- [ ] **Step 3: Implement deterministic scaffold and manifest**

Create thin Next Site projects that consume packed immutable packages, own route/brand/SEO/legal/locale/analytics, include their own
CI definition, and emit `site-web-artifact-manifest.json`. Implement `certify-external-sites.mjs` as the single lifecycle owner:
pack → generate → git init/commit → frozen clean install → build → launch on distinct ports → binding activate → cross-Site test →
independent rollback → shutdown/cleanup. Do not commit generated Site roots to `kokoro-web`; fixture JSON is input only. Persist only
sanitized manifests, exact package/lock/artifact/binding/commit digests, command results and rollback receipts under the declared
report directory.

- [ ] **Step 4: Verify two clean builds and isolation E2E**

Run: `pnpm -C kokoro-web test:repository && node kokoro-web/scripts/certify-external-sites.mjs --output kokoro-web/test/reports/external-sites`

Expected: PASS; both temporary repositories clean-build/deploy, cross-binding/Host/cookie access fails closed, each rollback is
independent, processes/temp package stores are cleaned, and all three sanitized reports validate against their schema.

- [ ] **Step 5: Commit boundary**

```bash
git -C kokoro-web add -- pnpm-lock.yaml packages/site-scaffold/package.json packages/site-scaffold/src/create-site-project.ts packages/site-scaffold/templates/site/package.json packages/site-scaffold/templates/site/next.config.ts packages/site-scaffold/templates/site/tsconfig.json packages/site-scaffold/templates/site/.github/workflows/site-ci.yml packages/site-scaffold/templates/site/public/icon.svg packages/site-scaffold/templates/site/src/app/globals.css packages/site-scaffold/templates/site/src/app/layout.tsx packages/site-scaffold/templates/site/src/app/page.tsx 'packages/site-scaffold/templates/site/src/app/api/session/[...path]/route.ts' packages/site-scaffold/templates/site/src/app/privacy/page.tsx packages/site-scaffold/templates/site/src/app/terms/page.tsx packages/site-scaffold/templates/site/src/analytics.ts packages/site-scaffold/templates/site/src/brand/tokens.css packages/site-scaffold/templates/site/src/i18n/en.json packages/site-scaffold/templates/site/src/lib/site-manifest.ts packages/site-scaffold/INDEX.md test/fixtures/external-sites/site-alpha.json test/fixtures/external-sites/site-beta.json test/repository/external-site-artifacts.test.mjs apps/user/tests/e2e/external-site-isolation.spec.ts scripts/certify-external-sites.mjs test/reports/external-sites/site-alpha.json test/reports/external-sites/site-beta.json test/reports/external-sites/summary.json
git -C kokoro-web commit -m "test(web): certify independent Site artifacts"
```

### Task 19: Promote runtime compatibility, clean cut, and evidence

**Repository:** Root, after Platform/Session/Web child commits and CI are green

**Files:**
- Rewrite: `scripts/compatibility/session-platform-internal-rpc.mjs`
- Rewrite: `scripts/compatibility/session-platform-internal-rpc.test.mjs`
- Modify: `config/repository/compatibility-matrix.json`
- Modify: `config/repository/federated-repositories.json`
- Modify in follow-up provenance commit: `config/repository/bom.json`
- Modify in follow-up provenance commit: `config/repository/expected-snapshots.json`
- Modify in follow-up provenance commit: `config/repository/frozen-submodules.yaml`
- Modify: `contract/registry/boundaries.yaml`
- Modify: `scripts/architecture/check_ga_isolation.py`
- Read-only verifier input: `docker-compose.infra.yml`
- Read-only verifier input: `config/repository/infrastructure-policy.yaml`
- Read-only verifier input: `scripts/infra/manager.mjs`
- Read-only verifier input: `scripts/infra/manager.test.mjs`
- Read-only verifier input: `scripts/infra/inventory.mjs`
- Read-only verifier input: `scripts/infra/inventory.test.mjs`
- Read-only verifier input: `scripts/infra/scope.mjs`
- Read-only verifier input: `scripts/infra/scope.test.mjs`
- Create: `scripts/wave3/verify-candidate.mjs`
- Create: `scripts/wave3/verify-candidate.test.mjs`
- Create: `docs/reports/evidence/wave-3/admission-runtime.md`
- Create: `docs/reports/evidence/wave-3/session-postgres-projection.md`
- Create: `docs/reports/evidence/wave-3/site-web-artifact-isolation.md`
- Modify: `docs/task.md`
- Modify gitlink: `kokoro-platform`
- Modify gitlink: `kokoro-session`
- Modify gitlink: `kokoro-web`

- [ ] **Step 1: Write red live-compatibility assertions**

Certify the Wave 1 default Infra result: PostgreSQL 18 has already replaced MySQL before Wave 3 begins. Wave 3 performs no second
database-topology migration. Assert Redis and GA/Hub Mongo remain byte-for-byte configured, MinIO remains the storage service,
MySQL has no active runtime profile, and existing Redis/Mongo/MinIO plus archived MySQL volumes/images/dev data are never deleted.
Start the real Platform Admission provider and real Session client; prove
Prepare→Finalize→dispatch intent, lost-response receipt recovery, wrong Site/audience/digest rejection, committed non-release, and
no GA wire change. Add matrix assertion IDs for provider/consumer and exact Infra inventory facts. Add candidate-verifier fixtures
that reject wrong SHA/pins, dirty children, GA control/golden-byte hash or status drift, missing external-Site reports, or any
destructive Infra action.

- [ ] **Step 2: Run red root tests**

Run: `node --test scripts/compatibility/session-platform-internal-rpc.test.mjs scripts/repository/run-pinned-compatibility.test.mjs scripts/infra/manager.test.mjs scripts/infra/inventory.test.mjs scripts/wave3/verify-candidate.test.mjs`

Expected: FAIL until the scenario uses the new provider/client and matrix declares `platform-admission`.

- [ ] **Step 3: Implement the compatibility scenario and candidate verifier**

Keep `platform-admission` contract-only until the live scenario passes locally. Then set registry lifecycle to active, add exact
provider/consumer protocol roles and required scenario, and prepare exact child artifact/tag digests and gitlinks for the candidate
commit. Read `docker-compose.infra.yml`, infrastructure policy, manager, scope and inventory only to certify the already-landed
Wave 1 PostgreSQL topology, signed leases, and retention behavior. Do not re-run MySQL→PostgreSQL migration or change Redis/Mongo/
MinIO image, config, network identity, volume identity, profiles or data; do not edit or stage any W1 Infra input. Archived MySQL
volume/image metadata is retained through the non-destructive inventory path; any attempted service/data deletion fails the gate. Implement
`verify-candidate.mjs` to rerun the gates against an explicit repository path and candidate SHA.

- [ ] **Step 4: Run child and root verification**

Run: `pnpm -C kokoro-platform test && pnpm -C kokoro-platform test:integration && pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`

Run: `npm --prefix kokoro-session audit --audit-level=high && npm --prefix kokoro-session run lint && npm --prefix kokoro-session run typecheck && npm --prefix kokoro-session test`

Run: `pnpm -C kokoro-web test && pnpm -C kokoro-web typecheck && pnpm -C kokoro-web lint && pnpm -C kokoro-web --filter @kokoro/web-user build`

Run: `uv run --locked python -m pytest contract/tests scripts/architecture/test_check_ga_isolation.py -q && node --test scripts/contract/*.test.mjs scripts/compatibility/*.test.mjs scripts/repository/*.test.mjs`

Run: `node scripts/repository/run-pinned-compatibility.mjs`

Expected: all PASS; compatibility output contains the new Admission assertions and all spawned processes/temporary databases are cleaned.

- [ ] **Step 5: Verify GA baseline and create the candidate promotion commit**

Run: `node scripts/wave3/preflight.mjs --verify-baseline .git/kokoro-wave3/baseline.json --ga-only`

This must prove exact Agent SHA, empty `git status --porcelain` including untracked files, unchanged SHA-256 for
`contract/spec/control.yaml` plus `kokoro-agent/src/kokoro_agent/contract/control.py`, and exact baseline matches for canonical
`run.request`/`run.cancel` golden-byte hashes. Generated-contract parity alone is insufficient. Any Agent gitlink/pin drift is an
immediate failure; `kokoro-agent` is verifier input and is never a promotion/staging path.

Stage only declared promotion paths and the three changed child gitlinks, then create the candidate before clean-clone verification:

```bash
git add -- contract/registry/boundaries.yaml config/repository/compatibility-matrix.json config/repository/federated-repositories.json scripts/compatibility/session-platform-internal-rpc.mjs scripts/compatibility/session-platform-internal-rpc.test.mjs scripts/architecture/check_ga_isolation.py scripts/wave3/verify-candidate.mjs scripts/wave3/verify-candidate.test.mjs kokoro-platform kokoro-session kokoro-web
git commit -m "feat(wave3): promote Session Admission and independent Site Web"
wave3_candidate_sha=$(git rev-parse HEAD)
```

- [ ] **Step 6: Verify the exact candidate SHA and rehearse a revert in a second clone**

Create two isolated directories with `mktemp -d`; clone the local repository recursively so the unpushed candidate object exists:

```bash
wave3_source_root=$(git rev-parse --show-toplevel)
wave3_candidate_clone=$(mktemp -d)
wave3_revert_clone=$(mktemp -d)
git clone --recurse-submodules "$wave3_source_root" "$wave3_candidate_clone/repo"
git -C "$wave3_candidate_clone/repo" checkout --detach "$wave3_candidate_sha"
git -C "$wave3_candidate_clone/repo" submodule update --init --recursive
node "$wave3_candidate_clone/repo/scripts/wave3/verify-candidate.mjs" --repo "$wave3_candidate_clone/repo" --candidate "$wave3_candidate_sha" --baseline "$wave3_source_root/.git/kokoro-wave3/baseline.json"
git clone --recurse-submodules "$wave3_source_root" "$wave3_revert_clone/repo"
git -C "$wave3_revert_clone/repo" checkout --detach "$wave3_candidate_sha"
git -C "$wave3_revert_clone/repo" switch -c wave3-rollback-rehearsal
git -C "$wave3_revert_clone/repo" revert --no-edit "$wave3_candidate_sha"
git -C "$wave3_revert_clone/repo" submodule update --init --recursive
node "$wave3_candidate_clone/repo/scripts/wave3/verify-candidate.mjs" --repo "$wave3_revert_clone/repo" --rollback-of "$wave3_candidate_sha" --baseline "$wave3_source_root/.git/kokoro-wave3/baseline.json"
```

Expected: candidate verification runs Step 4 gates against the exact SHA, including the complete GA baseline/golden-byte comparison;
the second clone creates a new revert commit, restores prior pins/registry/Infra, and passes rollback verification. Persist sanitized
SHA/result records, then remove only the validated temporary clone directories. Stop test processes/containers without deleting
volumes, images, or dev data.

- [ ] **Step 7: Write evidence, generate BOM/pin provenance, and create the follow-up promotion commit**

Each evidence file records child commit/tag, contract/generated digests, database/Node/package versions, exact commands and counts,
the three sanitized external-Site reports, SLO/load paths, GA SHA/status/two hashes/golden-byte proof, candidate and revert rehearsal
SHAs/results, preserved Infra inventory, and any external CI blocker.

Run the canonical repository generators against `wave3_candidate_sha`: update `bom.json` with exact child pins/artifact/evidence
digests and promotion SHA, then regenerate `expected-snapshots.json` and `frozen-submodules.yaml`. Never hand-edit generated pin/BOM
provenance. Verify the three files agree with the candidate gitlinks and pushed child tags before staging.

```bash
git add -- docs/reports/evidence/wave-3/admission-runtime.md docs/reports/evidence/wave-3/session-postgres-projection.md docs/reports/evidence/wave-3/site-web-artifact-isolation.md docs/task.md config/repository/bom.json config/repository/expected-snapshots.json config/repository/frozen-submodules.yaml
git commit -m "release(wave3): record evidence and pin provenance"
wave3_final_sha=$(git rev-parse HEAD)
```

- [ ] **Step 8: Verify and publish the exact final evidence HEAD**

Run `verify-candidate.mjs` again against a fresh recursive clone detached at `wave3_final_sha`, requiring the candidate/revert
receipts, evidence digests, BOM/pin/snapshot provenance, external-Site reports, Infra preservation facts, and complete GA baseline.
The final verifier must prove `wave3_final_sha` descends directly from the verified candidate and adds only the declared evidence/
provenance paths.

After human review, push the branch containing both Root commits. Wait for Root remote CI with the user-owned
`KOKORO_SUBMODULE_TOKEN` to pass against exact `wave3_final_sha`; missing token or a different tested SHA is a release blocker. Only
then create and push the annotated Root BOM tag bound to `wave3_final_sha` and the generated BOM digest. Never tag the first candidate
commit or an unverified evidence HEAD.

## Final release checklist

- [ ] Task 0 passed against approved/authorized Wave 1/W2A/W3 artifacts and recorded clean Root/four-child pins and evidence digests.
- [ ] Root contract and generated mirrors are byte-consistent; `platform-admission` became active only with real runtime evidence.
- [ ] Platform has one root Hold/Segment per execution root and same-key/same-payload receipts at every crash point.
- [ ] Session production uses PostgreSQL, complete snapshot, opaque cursor, bounded SSE, Inbox/Outbox/DLQ, and no commercial authority.
- [ ] Web uses the exact assistant-ui adapter boundary and no AssistantCloud/AssistantTransport persistence or transport.
- [ ] The single external-Site orchestrator proves two independent repositories, CI configs, frozen locks, artifacts, deployments,
      binding activations, cross-Site isolation and independent rollbacks, with sanitized persisted reports.
- [ ] Studio/Library/upload remain disabled without Wave 4 owner facts.
- [ ] `kokoro-agent` SHA and full porcelain status are unchanged; both recorded control hashes and both canonical GA golden-byte
      hashes match the Task 0 baseline.
- [ ] Wave 1's default PostgreSQL 18 topology is certified without a second migration; Redis/Mongo/MinIO and all archived volumes/
      images/dev data remain, MySQL has no active runtime profile, and no orphan test process/container remains.
- [ ] Child CI/tags are green; exact candidate SHA passed recursive-clone verification, a second clone passed revert rehearsal,
      the follow-up evidence/BOM/provenance HEAD passed a fresh-clone verifier and Root remote CI, and the pushed BOM tag binds that
      exact final SHA.
