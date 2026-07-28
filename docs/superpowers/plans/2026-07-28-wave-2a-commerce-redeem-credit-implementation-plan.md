# Wave 2A Commerce, Redeem, and Credit Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved `redeem_only` Commerce closure on the Wave 1 Platform PostgreSQL/UoW foundation, including immutable Catalog/Fulfillment, safe Code delivery, atomic Redeem, Subscription/Entitlement/Credit truth, Account UI, and certified Payment shutdown without changing GA.

**Architecture:** Root remains the only cross-repository contract authority. `kokoro-platform` implements Commerce as modules and cross-owner workflows over the single Wave 1 `PlatformUnitOfWork`; Credit owns one Journal/Hold/allocation/AuthorizationSegment model, while Wave 3 only adapts Session Admission to its typed application port. `kokoro-web` consumes generated contracts through Site-bound BFF routes, and Payment acquisition remains absent at route, domain, worker, secret, Admin, and deployment layers.

**Tech Stack:** Inherit the qualified Wave 1 runtime exactly: Node.js 22, TypeScript 5.9, the Wave 1 pinned Zod major, Vitest,
Prisma 7, PostgreSQL 18, Fastify/OpenAPI, ConnectRPC/Protobuf, RFC 8785 JCS, Redis-backed rate limiting only, S3-compatible
encrypted object storage, Next.js 16.2, React 19.2, Playwright, and pnpm 11. Wave 2A is not a Node or Zod upgrade wave.

---

## Preconditions and non-negotiable gates

- Authority spec: `docs/superpowers/specs/2026-07-28-wave-2a-commerce-redeem-credit-design.md` with `status: internally-approved`, `implementationAuthorized: true`, and `gaRuntimeSemanticChangeAuthorized: false`.
- Wave 1 must have landed the single `kokoro-platform/prisma/schema.prisma`, `src/shared/unit-of-work`, `src/shared/security-context`, `src/shared/outbox-inbox`, `src/process/{api,worker}.ts`, PostgreSQL roles, Site/Identity/Workspace/Policy/Admin owner ports, and personal `BillingAccount` bootstrap. Missing Wave 1 artifacts block Task 1; do not recreate them under Commerce.
- Root contract/config/evidence files have one named integrator/writer for the whole Wave. Platform and Web generated mirrors may
  change only after the corresponding Root contract commit exists; generated files are never edited by hand.
- `kokoro-platform` uses only `DATABASE_URL_PLATFORM`. No Commerce task may add a module database, self-RPC, `*_BASE_URL`, raw Prisma client crossing an owner boundary, or a second transaction manager.
- Credit owns the only `CreditGrant`, append-only Journal, root `CreditHold`, `HoldAllocation`, `ExecutionBudgetRoot`, allocation revision, and `AuthorizationSegment`. Wave 3 must consume the typed local port; it must not create a second table or ledger.
- Before Task 1 the Root integrator commits a machine-readable GA baseline containing Agent gitlink HEAD/tree, expected clean
  status, canonical `run.request` and `run.cancel` wire hashes, both control source/generated-mirror hashes, and the forbidden
  Commerce-field scan result. Every chunk runs the same checker; printing a SHA is not evidence.
- Use the one Root-managed default Infra stack. Only the Root integrator may inspect/reconcile/start/stop it; implementation workers
  receive an isolated leased Platform database/schema and never invoke Docker/Compose. Real PostgreSQL tests first validate the
  signed lease and `DATABASE_URL_PLATFORM_TEST`; missing/unreachable PostgreSQL is an explicit failure, never a skip. Cleanup may
  release only that lease and stop surplus verification containers; it never prunes volumes/images or developer data.
- Every task follows red test -> focused green -> local suite -> commit. Workers commit only in their owning repository; only the final integrator updates root gitlinks.
- Generated clients target the Wave 1 Zod API. If generation genuinely requires a Zod-major change, stop and add a separate
  same-repository dependency task that modifies `package.json` and lockfile, proves generated/runtime compatibility, and passes the
  full repository suite; do not smuggle a dependency or Node upgrade into a feature task.

## Execution DAG and writer leases

No task below owns more than one Git repository. The only permitted parallelism is between different repositories after their
declared Root/provider dependency is committed. Within a child repository one named worker holds the writer lease and executes its
chain serially:

```text
Root R0 GA/Infra guard → R1 public contract → R2 generator/parity authority
                                      ├→ Platform P1 generated mirror
                                      │   → P2 storage/fence → P3 Catalog/Fulfillment → P4 Code/export
                                      │   → P5 Redeem/review → P6 Subscription/Entitlement → P7 Credit
                                      │   → P8 Outbox/reconcile → P9 reversal/read providers → P10 Admin/Support
                                      │   → P11 Payment mutation gate → P12 clean-cut certification
                                      └→ Web W1 generated mirror
                                          → W2 Admin (after P10) → W3 Payment mutation gate (after P11)
                                          → W4 Account/Redeem (after P9)

P12 + W4 + all child remote CI/tag/push
→ Root R3 compatibility/default-Infra/clean-clone/rollback/pin+BOM promotion
```

Tasks sharing `kokoro-platform/prisma/schema.prisma`, `src/process/*`, Platform package metadata, Web app trees, or Root registry/config
are never dispatched concurrently. Root R3 is the only gitlink/pin/BOM writer.

### Root Task R0: Freeze the GA baseline and default-Infra guard

**Repository:** Root

**Files:**
- Create: `config/repository/wave-2a-ga-baseline.json`
- Create: `scripts/verification/wave-2a-guard.mjs`
- Create: `scripts/verification/wave-2a-guard.test.mjs`
- Create: `scripts/verification/fixtures/wave-2a-ga/**`

- [ ] Write failing fixture tests proving the checker rejects changed Agent HEAD or tree, dirty/cached files, either changed control
wire, changed canonical `run.request`/`run.cancel` bytes, and any Commerce/Credit/allocation field added to GA. Add Infra tests that
reject non-default projects, unsigned/stale leases, unavailable PostgreSQL, and cleanup outside the leased identifiers.
- [ ] Run `node --test scripts/verification/wave-2a-guard.test.mjs`; confirm RED because the guard and baseline do not exist.
- [ ] Implement `ga-record` once, `ga-check`, `infra-inspect`, `infra-reconcile`, `lease-acquire`, `lease-check`, and `lease-release`
over the Wave 1 Root manager/scope APIs. `infra-reconcile` is main-integrator-only; worker commands can only call `lease-check`.
- [ ] As Root integrator run `infra-inspect`, reconcile exactly one default Platform Infra stack if required, acquire the Wave 2A
leased PostgreSQL target, and record its opaque lease file outside Git. Prove a connection query before any `[PG]` test.
- [ ] Commit only Root guard/baseline files. Run `ga-check` and `lease-check` at the start and end of every chunk.

## File ownership map

| Surface | Ownership |
|---|---|
| Root public contract | `contract/openapi/platform-public-v1.yaml`, registry, deterministic generator, generated parity tests |
| Platform storage/UoW | `kokoro-platform/prisma/**`, `src/shared/{unit-of-work,outbox-inbox}/**`, Commerce-owned repository factories |
| Catalog/Fulfillment | `src/modules/{catalog,commerce}/**`, `src/workflows/fulfillment/**` |
| Code inventory/export | `src/modules/redeem/{domain,application,infrastructure}/**`, `src/interfaces/workers/redeem/**` |
| Redeem | `src/workflows/redeem/**`, `src/interfaces/http/redeem/**` |
| Subscription/Entitlement/Allowance | `src/modules/{commerce,credit}/**`, `src/workflows/program-window/**` |
| Credit/Admission | `src/modules/credit/**`, `src/workflows/execution-budget/**`; no Session or GA implementation |
| Outbox/reconciliation | `src/shared/outbox-inbox/**`, `src/workflows/reconciliation/**`, worker assembly |
| Admin/Support | Platform Commerce manifests/commands plus Admin Web generated-client pages; no direct DB access |
| Payment closure | repository/deploy/route/env/SBOM negative gates; no Payment authority implementation |
| Site Web | `kokoro-web/apps/user` Account/Redeem BFF and UI consuming generated Root contract |
| Certification | migration preflight, default Infra, evidence, compatibility matrix, child pins |

## Chunk 1: Root contract, Platform schema, and transaction foundations

### Root Task R1: Extend the public Platform contract with Commerce

**Repository:** Root

**Files:**
- Modify: `contract/openapi/platform-public-v1.yaml`
- Modify: `contract/registry/boundaries.yaml`
- Create: `contract/tests/test_platform_public_contract.py`
- Modify: `contract/tests/test_generate.py`
- Create: `scripts/contract/generate-platform-public.mjs`
- Create: `scripts/contract/generate-platform-public.test.mjs`
- Modify: `scripts/contract/check-boundary-registry.test.mjs`

- [ ] **Step 1: Write the failing contract tests**

Assert the OpenAPI source defines strict request/response schemas for preview, confirm, command recovery, receipt, account products,
credit summary, grant detail, and usage detail. Assert mutation bodies contain no `siteId`, `billingAccountId`, owner, Payment,
provider, raw Code echo, or GA field; mutation metadata requires workload-bound actor context, CSRF, contract revision, and
`Idempotency-Key`. Assert the registry provider is `service.platform`, consumer is Site Web BFF, lifecycle remains
`contract-only`, and every operation declares retry/receipt/deadline behavior.

- [ ] **Step 2: Validate the default-Infra lease, then run the red tests**

Run: `uv run --locked python -m pytest contract/tests/test_platform_public_contract.py contract/tests/test_generate.py -q`

Run separately even after the expected Python failure: `node --test scripts/contract/generate-platform-public.test.mjs scripts/contract/check-boundary-registry.test.mjs`

Expected: each command FAILS for an asserted Commerce-operation/schema/generator capability that is missing from the existing Wave 1
OpenAPI source. “File not found”, test discovery failure, dependency failure, or the whole Wave 1 source being absent is not an
acceptable RED.

- [ ] **Step 3: Add the minimum authoritative contract and generator**

Define stable codes including `REDEEM_NOT_ACCEPTED`, `REDEEM_TEMPORARILY_UNAVAILABLE`, `IDEMPOTENCY_CONFLICT`,
`ACQUISITION_CHANNEL_DISABLED`, and typed receipt states. Generate strict Zod/types into the Wave 1 provider and Site Web target
directories with a source digest banner. Do not define Payment acquisition, Session Admission RPC, or GA fields in this contract.

- [ ] **Step 4: Verify contract and byte parity**

Run: `uv run --locked python -m pytest contract/tests/test_platform_public_contract.py contract/tests/test_generate.py -q`

Run: `node --test scripts/contract/*.test.mjs && node scripts/contract/check-boundary-registry.mjs`

Expected: PASS; a second generator run produces no diff and Commerce remains `contract-only`.

- [ ] **Step 5: Commit the Root authority boundary**

```bash
git add -- contract/openapi/platform-public-v1.yaml contract/registry/boundaries.yaml contract/tests/test_platform_public_contract.py contract/tests/test_generate.py scripts/contract/generate-platform-public.mjs scripts/contract/generate-platform-public.test.mjs scripts/contract/check-boundary-registry.test.mjs
git commit -m "feat(contract): freeze redeem-only commerce API"
```

### Root Task R2: Certify generated-mirror governance

**Repository:** Root

**Files:**
- Modify: `scripts/repository/check-generated-contracts.mjs`
- Modify: `scripts/repository/check-generated-contracts.test.mjs`

- [ ] **Step 1: Add red source-digest and stale-mirror tests**

Require provider and consumer mirror manifests to carry the Root OpenAPI digest and the exact eight resource groups. Add isolated
temporary generated/tampered fixtures that must fail `check-generated-contracts`; prove the validator rejects a stale digest,
missing operation, extra operation, and handwritten shape even when TypeScript types happen to match.

- [ ] **Step 2: Run the red tests**

Run: `node --test scripts/repository/check-generated-contracts.test.mjs`

Expected: FAIL on a named missing Commerce mirror-manifest/checker rule, not because child repositories or dependencies are absent.

- [ ] **Step 3: Generate both mirrors without handwritten edits**

Run the Root generator against temporary fixtures and commit only the source digest/target manifest/checker authority in Root. This
task does not write or commit either child repository. No child may import `contract/` at runtime or import a sibling source path.

- [ ] **Step 4: Verify each owning repository**

Run: `node --test scripts/repository/check-generated-contracts.test.mjs`

Expected: PASS and a second fixture generation is byte-stable.

- [ ] **Step 5: Commit the Root generator/checker authority**

```bash
git add -- scripts/repository/check-generated-contracts.mjs scripts/repository/check-generated-contracts.test.mjs && git commit -m "build(contract): verify commerce mirrors"
```

### Platform Task P1: Generate and commit the provider mirror

**Repository:** `kokoro-platform`

**Depends on:** Root R1 and R2 committed.

**Files:**
- Create: `kokoro-platform/src/interfaces/http/generated/platform-public-v1.ts`
- Create: `kokoro-platform/test/contract/platform-public-generated.test.ts`

- [ ] Write a failing source-digest/operation-set test; confirm RED specifically because the provider mirror is absent/stale.
- [ ] Run the committed Root generator targeting Platform; do not hand edit the result or import Root at runtime.
- [ ] Run `pnpm -C kokoro-platform exec vitest run test/contract/platform-public-generated.test.ts`, the Root parity checker, typecheck,
and lint. Regenerate twice and require an empty child diff on the second run.
- [ ] Commit only Platform files:
```bash
git -C kokoro-platform add -- src/interfaces/http/generated/platform-public-v1.ts test/contract/platform-public-generated.test.ts
git -C kokoro-platform commit -m "build: generate commerce provider contract"
```

### Web Task W1: Generate and commit the Site Web consumer mirror

**Repository:** `kokoro-web`

**Depends on:** Root R1 and R2 committed.

**Files:**
- Create: `kokoro-web/apps/user/src/generated/platform-public-v1.ts`
- Create: `kokoro-web/apps/user/tests/contract/platform-public-generated.test.ts`

- [ ] Write a failing source-digest/exact-eight-operation test; confirm RED specifically because the consumer mirror is absent/stale.
- [ ] Run the committed Root generator targeting Web. Generate against the Wave 1 pinned Zod API; do not change Node/Zod silently.
- [ ] Run the focused Vitest, Root parity checker, Web typecheck/lint, and a second byte-stable generation.
- [ ] Commit only Web files:
```bash
git -C kokoro-web add -- apps/user/src/generated/platform-public-v1.ts apps/user/tests/contract/platform-public-generated.test.ts
git -C kokoro-web commit -m "build: generate commerce web contract"
```

### Platform Task P2: Extend the Wave 1 schema for Commerce command and output truth

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_commerce_core/migration.sql`
- Create: `kokoro-platform/src/modules/commerce/domain/command-identity.ts`
- Create: `kokoro-platform/src/modules/commerce/domain/output-line.ts`
- Create: `kokoro-platform/src/modules/commerce/application/contracts/repository.ts`
- Create: `kokoro-platform/src/modules/commerce/infrastructure/postgres/repository.ts`
- Create: `kokoro-platform/src/modules/commerce/INDEX.md`
- Create: `kokoro-platform/test/unit/commerce-command-identity.test.ts`
- Create: `kokoro-platform/test/integration/commerce-schema.test.ts`

- [ ] **Step 1: Write red domain and real-PostgreSQL tests**

Cover Site-scoped command identity, same-key/same-digest replay, different-digest conflict before business locks, immutable
`outputLineId`, continuous ordinal, occurrence/cardinality bounds, source-purpose-cycle uniqueness, fixed-length digests, composite
Site FKs, rollback, and application role without DDL or `BYPASSRLS`.

- [ ] **Step 2: Run the red tests**

Run: `pnpm -C kokoro-platform exec vitest run test/unit/commerce-command-identity.test.ts test/integration/commerce-schema.test.ts`

Expected: FAIL because the Commerce tables and repository are absent. Missing PostgreSQL is a failure, not a skip.

- [ ] **Step 3: Add the minimum schema and owner repository**

Add `commerce_idempotency_record`, immutable version/source tables, fulfillment transaction/output-line rows, command result,
receipt, audit, and owned outbox FKs. The repository receives the opaque Wave 1 `PlatformTransaction`; it must not accept or expose
a Prisma client. Add SQL constraints for digest length, canonical identity, status transitions, and output multiset uniqueness.

- [ ] **Step 4: Verify Prisma and transaction behavior**

Run: `pnpm -C kokoro-platform exec prisma validate --schema prisma/schema.prisma && pnpm -C kokoro-platform exec prisma generate --schema prisma/schema.prisma`

Run: `pnpm -C kokoro-platform exec vitest run test/unit/commerce-command-identity.test.ts test/integration/commerce-schema.test.ts`

Expected: PASS, including transaction rollback and lock-order probes.

- [ ] **Step 5: Commit the storage slice**

```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_commerce_core/migration.sql' src/modules/commerce/domain/command-identity.ts src/modules/commerce/domain/output-line.ts src/modules/commerce/application/contracts/repository.ts src/modules/commerce/infrastructure/postgres/repository.ts src/modules/commerce/INDEX.md test/unit/commerce-command-identity.test.ts test/integration/commerce-schema.test.ts
git -C kokoro-platform commit -m "feat(commerce): add command and fulfillment persistence"
```

### Platform Task P2B: Add Commerce transaction ports and effect-point authorization

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/src/modules/commerce/application/contracts/catalog-port.ts`
- Create: `kokoro-platform/src/modules/commerce/application/contracts/subscription-port.ts`
- Create: `kokoro-platform/src/modules/commerce/application/contracts/credit-port.ts`
- Create: `kokoro-platform/src/modules/commerce/application/command-fence.ts`
- Create: `kokoro-platform/src/workflows/commerce/authorize-command.ts`
- Create: `kokoro-platform/src/workflows/commerce/lock-order.ts`
- Create: `kokoro-platform/src/workflows/commerce/INDEX.md`
- Create: `kokoro-platform/test/unit/commerce-command-fence.test.ts`
- Create: `kokoro-platform/test/integration/commerce-lock-order.test.ts`
- Create: `kokoro-platform/test/security/commerce-effect-auth.test.ts`

- [ ] **Step 1: Write failing fence, lock, and Site-auth tests**

Prove unique command claim/lock occurs before Program, Batch, Code, BillingAccount, Subscription, Grant, Hold, or allocation locks.
Cover forged header/body Site, stale binding/security/restriction epoch, cross-environment/region, wrong audience, anonymous confirm,
missing CSRF, and typed `SiteScope|GlobalScope|BreakGlassScope` confusion. BreakGlass must never imply Global or enable Payment.

- [ ] **Step 2: Run the red tests**

Run: `pnpm -C kokoro-platform exec vitest run test/unit/commerce-command-fence.test.ts test/integration/commerce-lock-order.test.ts test/security/commerce-effect-auth.test.ts`

Expected: FAIL because the Commerce command fence and owner ports are missing.

- [ ] **Step 3: Implement the minimum command executor**

Use the Wave 1 canonical request security evaluator. Atomically claim `(environment,siteId,actor,operation,key)`, compare the
canonical digest, then enter the frozen lock DAG. Inject only transaction-scoped owner ports; never call Platform HTTP from
Platform or authorize from caller-provided identity fields.

- [ ] **Step 4: Verify focused and architecture tests**

Run: `pnpm -C kokoro-platform exec vitest run test/unit/commerce-command-fence.test.ts test/integration/commerce-lock-order.test.ts test/security/commerce-effect-auth.test.ts`

Run: `pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`

Expected: PASS; different-digest conflicts acquire no business authority lock.

- [ ] **Step 5: Commit the workflow boundary**

```bash
git -C kokoro-platform add -- src/modules/commerce/application/contracts/catalog-port.ts src/modules/commerce/application/contracts/subscription-port.ts src/modules/commerce/application/contracts/credit-port.ts src/modules/commerce/application/command-fence.ts src/workflows/commerce/authorize-command.ts src/workflows/commerce/lock-order.ts src/workflows/commerce/INDEX.md test/unit/commerce-command-fence.test.ts test/integration/commerce-lock-order.test.ts test/security/commerce-effect-auth.test.ts
git -C kokoro-platform commit -m "feat(commerce): fence commands and effect authorization"
```

At the Chunk 1 exit, the Root integrator runs `ga-check`; the Platform worker runs `lease-check`, its complete local suite, and
returns the writer lease before another Platform worker can start.

## Chunk 2: Commerce capabilities

### Platform Task P3: Implement immutable Catalog, SalesPolicy, and exact Fulfillment

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_catalog_fulfillment/migration.sql`
- Create: `kokoro-platform/src/modules/catalog/domain/versions.ts`
- Create: `kokoro-platform/src/modules/catalog/application/catalog-service.ts`
- Create: `kokoro-platform/src/modules/catalog/application/sales-policy-compiler.ts`
- Create: `kokoro-platform/src/modules/catalog/infrastructure/postgres/repository.ts`
- Create: `kokoro-platform/src/modules/catalog/INDEX.md`
- Create: `kokoro-platform/src/workflows/fulfillment/execute-fulfillment.ts`
- Create: `kokoro-platform/src/workflows/fulfillment/output-multiset.ts`
- Create: `kokoro-platform/src/workflows/fulfillment/INDEX.md`
- Create: `kokoro-platform/test/unit/fulfillment-output-plan.test.ts`
- Create: `kokoro-platform/test/integration/fulfillment-atomicity.test.ts`
- Create: `kokoro-platform/test/integration/catalog-sales-policy-postgres.test.ts`

- [ ] **Step 1: Write red tests** for immutable published versions, Product-kind discriminants, unique `outputLineId`, cardinality,
template revision, required/optional/forbidden exact multiset, source-purpose-cycle replay, and rollback on any missing/extra output.
The real-PostgreSQL test owns this task's schema diff and constraints for Product/Plan/Offering/Fulfillment versions, output lines,
SalesPolicyRevision/SiteRelease assignment, legal Merchant liability, publish immutability, Site composite FKs, and CAS.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/unit/fulfillment-output-plan.test.ts test/integration/fulfillment-atomicity.test.ts test/integration/catalog-sales-policy-postgres.test.ts`
Expected: FAIL because Catalog/Fulfillment owners are absent.
- [ ] **Step 3: Implement minimally** with owner repositories and one cross-owner `PlatformUnitOfWork`; freeze the same output-set
digest in fulfillment, receipt, audit, idempotency result, and outbox. Compile `acquisitionMode=redeem_only`, allowed Program versions,
zero Provider assignment, Offering/Product/Plan compatibility, and legal liability into SiteRelease. Never infer output from a mutable
current Plan or pre-create a later owner's tables.
- [ ] **Step 4: Verify:** rerun the focused command, then `pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_catalog_fulfillment/migration.sql' src/modules/catalog/domain/versions.ts src/modules/catalog/application/catalog-service.ts src/modules/catalog/application/sales-policy-compiler.ts src/modules/catalog/infrastructure/postgres/repository.ts src/modules/catalog/INDEX.md src/workflows/fulfillment/execute-fulfillment.ts src/workflows/fulfillment/output-multiset.ts src/workflows/fulfillment/INDEX.md test/unit/fulfillment-output-plan.test.ts test/integration/fulfillment-atomicity.test.ts test/integration/catalog-sales-policy-postgres.test.ts
git -C kokoro-platform commit -m "feat(catalog): execute immutable fulfillment plans"
```

### Platform Task P4: Implement Code inventory, encrypted export, and activation commitment

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_redeem_inventory_export/migration.sql`
- Create: `kokoro-platform/src/modules/redeem/domain/code-format.ts`
- Create: `kokoro-platform/src/modules/redeem/domain/batch.ts`
- Create: `kokoro-platform/src/modules/redeem/application/generate-batch.ts`
- Create: `kokoro-platform/src/modules/redeem/application/deliver-export.ts`
- Create: `kokoro-platform/src/modules/redeem/infrastructure/object-store/encrypted-export.ts`
- Create: `kokoro-platform/src/interfaces/workers/redeem/export-worker.ts`
- Create: `kokoro-platform/src/modules/redeem/INDEX.md`
- Create: `kokoro-platform/test/unit/redeem-code-format.test.ts`
- Create: `kokoro-platform/test/integration/batch-export-delivery.test.ts`
- Create: `kokoro-platform/test/security/code-plaintext-scan.test.ts`

- [ ] **Step 1: Write red unit and leased real-PostgreSQL tests** for entropy/locator bounds, HMAC domain separation, constant-time match, ordered inventory root,
artifact hash/ETag/size commitment, maker-checker, one delivery claim/stream, monotonic Range CAS, unknown->suspend, crypto-shred +
object-version GC receipts, and activation only when the complete delivered commitment matches. The migration owns Program/Batch/Code,
inventory commitment, artifact, claim/session/GC receipt constraints and Site FKs. Scan DB/log/event/error fixtures for plaintext.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/unit/redeem-code-format.test.ts test/integration/batch-export-delivery.test.ts test/security/code-plaintext-scan.test.ts`
Expected: FAIL because inventory/export owners are missing.
- [ ] **Step 3: Implement minimally** using streaming encryption and Secret Manager key refs; never write plaintext to disk, DB,
backup, log, or Admin. `expired|unknown` cannot activate or regenerate the same Batch.
- [ ] **Step 4: Verify:** rerun focused tests and confirm every orphan fixture receives a typed disposal receipt.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_redeem_inventory_export/migration.sql' src/modules/redeem/domain/code-format.ts src/modules/redeem/domain/batch.ts src/modules/redeem/application/generate-batch.ts src/modules/redeem/application/deliver-export.ts src/modules/redeem/infrastructure/object-store/encrypted-export.ts src/interfaces/workers/redeem/export-worker.ts src/modules/redeem/INDEX.md test/unit/redeem-code-format.test.ts test/integration/batch-export-delivery.test.ts test/security/code-plaintext-scan.test.ts
git -C kokoro-platform commit -m "feat(redeem): secure batch generation and delivery"
```

### Platform Task P5: Implement Preview, review approval, atomic Confirm, recovery, and receipt APIs

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_redemption_workflow/migration.sql`
- Create: `kokoro-platform/src/workflows/redeem/preview-redemption.ts`
- Create: `kokoro-platform/src/workflows/redeem/confirm-redemption.ts`
- Create: `kokoro-platform/src/workflows/redeem/review-redemption.ts`
- Create: `kokoro-platform/src/workflows/redeem/recover-command.ts`
- Create: `kokoro-platform/src/workflows/redeem/get-redemption-receipt.ts`
- Create: `kokoro-platform/src/workflows/redeem/INDEX.md`
- Create: `kokoro-platform/src/interfaces/http/redeem/routes.ts`
- Modify: `kokoro-platform/src/process/api.ts`
- Create: `kokoro-platform/test/integration/redeem-confirm-postgres.test.ts`
- Create: `kokoro-platform/test/integration/redeem-http.test.ts`
- Create: `kokoro-platform/test/integration/redeem-review-recovery.test.ts`
- Create: `kokoro-platform/test/property/redeem-concurrency.test.ts`

- [ ] **Step 1: Write red tests** covering preview no-claim, bounded locator, Risk fail-closed, single concurrent winner, same-key replay,
different-digest conflict before Code lock, same-Plan stacking, Plan mismatch without claim, failure injection at every write, lost HTTP
response, cross-Site non-disclosure, and zero partial Grant/Journal/outbox state. Add `RedemptionAttempt/RiskCase` no-claim behavior,
single-use/expiring `RedeemApprovalGrant`, stale RestrictionEpoch denial, full revalidation on resume, and approval losing safely when
another actor redeemed the Code. This task's migration owns Redemption/Attempt/RiskCase/ApprovalGrant facts and constraints.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/integration/redeem-confirm-postgres.test.ts test/integration/redeem-http.test.ts test/integration/redeem-review-recovery.test.ts test/property/redeem-concurrency.test.ts`
Expected: FAIL because the workflow/routes are absent.
- [ ] **Step 3: Implement minimally** in the frozen lock order; review creates no claim/reserve, while approved resume still executes
the entire confirm UoW. Create Redemption, exact Fulfillment, receipt, audit, terminal idempotency result, and outbox atomically. HTTP
adapters derive owner/Site from verified context only.
- [ ] **Step 4: Verify:** rerun focused tests, then `pnpm -C kokoro-platform test:integration`.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_redemption_workflow/migration.sql' src/workflows/redeem/preview-redemption.ts src/workflows/redeem/confirm-redemption.ts src/workflows/redeem/review-redemption.ts src/workflows/redeem/recover-command.ts src/workflows/redeem/get-redemption-receipt.ts src/workflows/redeem/INDEX.md src/interfaces/http/redeem/routes.ts src/process/api.ts test/integration/redeem-confirm-postgres.test.ts test/integration/redeem-http.test.ts test/integration/redeem-review-recovery.test.ts test/property/redeem-concurrency.test.ts
git -C kokoro-platform commit -m "feat(redeem): claim and fulfill codes atomically"
```

### Platform Task P6: Add Subscription, Entitlement, and Allowance owners

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_subscription_entitlement/migration.sql`
- Create: `kokoro-platform/src/modules/commerce/domain/subscription.ts`
- Create: `kokoro-platform/src/modules/commerce/domain/entitlement.ts`
- Create: `kokoro-platform/src/modules/commerce/application/subscription-service.ts`
- Create: `kokoro-platform/src/workflows/program-window/materialize-window.ts`
- Create: `kokoro-platform/src/workflows/program-window/INDEX.md`
- Create: `kokoro-platform/test/unit/subscription-policy.test.ts`
- Create: `kokoro-platform/test/integration/subscription-entitlement.test.ts`
- Create: `kokoro-platform/test/property/program-window.test.ts`

- [ ] **Step 1: Write red unit and leased real-PostgreSQL tests** for stable active slot, `extend_from_max`, max expiry/stack count,
different-Plan rejection, source-specific immutable term/entitlement, daily/period/permanent window identity, concurrent window single
winner, and source reversal. This migration owns Subscription/slot/binding/term, Entitlement/Revocation and ProgramWindow identities.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/unit/subscription-policy.test.ts test/integration/subscription-entitlement.test.ts test/property/program-window.test.ts`
Expected: FAIL because these owner services are missing.
- [ ] **Step 3: Implement minimally** with ordinary unique/CAS constraints, versioned policies, ProgramWindow acquisition, and append-only
revocation facts; do not use time-dependent partial unique indexes or mutable bucket authority.
- [ ] **Step 4: Verify:** rerun focused tests and Prisma validation.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_subscription_entitlement/migration.sql' src/modules/commerce/domain/subscription.ts src/modules/commerce/domain/entitlement.ts src/modules/commerce/application/subscription-service.ts src/workflows/program-window/materialize-window.ts src/workflows/program-window/INDEX.md test/unit/subscription-policy.test.ts test/integration/subscription-entitlement.test.ts test/property/program-window.test.ts
git -C kokoro-platform commit -m "feat(commerce): materialize terms entitlements and allowances"
```

### Platform Task P7: Implement the sole Credit and Admission budget authority

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_credit_authority/migration.sql`
- Create: `kokoro-platform/src/modules/credit/domain/journal.ts`
- Create: `kokoro-platform/src/modules/credit/domain/allocation.ts`
- Create: `kokoro-platform/src/modules/credit/domain/authorization-segment.ts`
- Create: `kokoro-platform/src/modules/credit/application/contracts/run-budget-authority.ts`
- Create: `kokoro-platform/src/modules/credit/application/credit-service.ts`
- Create: `kokoro-platform/src/modules/credit/infrastructure/postgres/repository.ts`
- Create: `kokoro-platform/src/modules/credit/INDEX.md`
- Create: `kokoro-platform/src/workflows/execution-budget/commands.ts`
- Create: `kokoro-platform/src/workflows/execution-budget/INDEX.md`
- Create: `kokoro-platform/test/property/credit-conservation.test.ts`
- Create: `kokoro-platform/test/integration/execution-budget-postgres.test.ts`

- [ ] **Step 1: Write red property/PostgreSQL tests** for balanced Journal, deterministic Grant burn, exact HoldAllocation, one
ExecutionBudgetRoot/root Hold, stock-vs-cumulative node/tree conservation, child return exactly once, Segment slice
reserved->committed CAS, committed non-TTL-release, unknown reconciliation, and no second root/ledger. This migration owns the sole
CreditAccount/Grant/Journal/Hold/HoldAllocation/ExecutionBudgetRoot/allocation revision/AuthorizationSegment schema and SQL invariants.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/property/credit-conservation.test.ts test/integration/execution-budget-postgres.test.ts`
Expected: FAIL because the Wave 2A Credit authority is absent.
- [ ] **Step 3: Implement minimally** behind `RunBudgetAuthority`; keep root Hold open while committing only the Segment slice.
Wave 3 may call this port inside the same UoW but may not import Credit infrastructure or create its own segment table.
- [ ] **Step 4: Verify:** rerun focused tests plus `pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_credit_authority/migration.sql' src/modules/credit/domain/journal.ts src/modules/credit/domain/allocation.ts src/modules/credit/domain/authorization-segment.ts src/modules/credit/application/contracts/run-budget-authority.ts src/modules/credit/application/credit-service.ts src/modules/credit/infrastructure/postgres/repository.ts src/modules/credit/INDEX.md src/workflows/execution-budget/commands.ts src/workflows/execution-budget/INDEX.md test/property/credit-conservation.test.ts test/integration/execution-budget-postgres.test.ts
git -C kokoro-platform commit -m "feat(credit): own journals holds and authorization slices"
```

### Platform Task P8: Add canonical Outbox, Inbox, DLQ, and reconciliation

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_commerce_outbox_reconciliation/migration.sql`
- Create: `kokoro-platform/src/shared/outbox-inbox/canonical-digest.ts`
- Create: `kokoro-platform/src/shared/outbox-inbox/relay.ts`
- Create: `kokoro-platform/src/shared/outbox-inbox/inbox.ts`
- Create: `kokoro-platform/src/workflows/reconciliation/commerce-reconciler.ts`
- Create: `kokoro-platform/src/workflows/reconciliation/INDEX.md`
- Modify: `kokoro-platform/src/process/worker.ts`
- Create: `kokoro-platform/test/unit/canonical-envelope-digest.test.ts`
- Create: `kokoro-platform/test/integration/outbox-inbox-worker.test.ts`
- Create: `kokoro-platform/test/integration/commerce-reconciliation.test.ts`

- [ ] **Step 1: Write red tests** for deterministic Protobuf/JCS payload bytes, envelope domain separation, same event/same digest replay,
different digest quarantine, `SKIP LOCKED` lease/takeover, checkpoint only after ack, consumer Inbox atomicity, DLQ ownership, and
reconciler producing typed Case/repair commands rather than direct table updates. This task owns only its Outbox/Inbox/DLQ/checkpoint/
quarantine/ReconciliationCase schema diff; it extends, rather than forks, the Wave 1 shared tables.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:** `pnpm -C kokoro-platform exec vitest run test/unit/canonical-envelope-digest.test.ts test/integration/outbox-inbox-worker.test.ts test/integration/commerce-reconciliation.test.ts`
Expected: FAIL because the worker implementations are missing.
- [ ] **Step 3: Implement minimally** and register worker readiness/drain; preserve receipt recovery even while relay is unavailable.
- [ ] **Step 4: Verify:** rerun focused tests, then `pnpm -C kokoro-platform test:integration`.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_commerce_outbox_reconciliation/migration.sql' src/shared/outbox-inbox/canonical-digest.ts src/shared/outbox-inbox/relay.ts src/shared/outbox-inbox/inbox.ts src/workflows/reconciliation/commerce-reconciler.ts src/workflows/reconciliation/INDEX.md src/process/worker.ts test/unit/canonical-envelope-digest.test.ts test/integration/outbox-inbox-worker.test.ts test/integration/commerce-reconciliation.test.ts
git -C kokoro-platform commit -m "feat(platform): relay and reconcile commerce facts"
```

### Platform Task P9: Complete source recovery, campaigns, projections, and all public read providers

**Repository:** `kokoro-platform`

**Files:**
- Modify: `kokoro-platform/prisma/schema.prisma`
- Create: `kokoro-platform/prisma/migrations/<timestamp>_wave_2a_reversal_campaign_reads/migration.sql`
- Create: `kokoro-platform/src/workflows/redemption-reversal/reverse-redemption.ts`
- Create: `kokoro-platform/src/workflows/redemption-reversal/issue-replacement.ts`
- Create: `kokoro-platform/src/workflows/redemption-reversal/run-batch-campaign.ts`
- Create: `kokoro-platform/src/workflows/redemption-reversal/INDEX.md`
- Create: `kokoro-platform/src/modules/commerce/application/account-read-service.ts`
- Create: `kokoro-platform/src/modules/commerce/infrastructure/postgres/account-projection-repository.ts`
- Create: `kokoro-platform/src/interfaces/http/commerce/account-routes.ts`
- Create: `kokoro-platform/test/integration/redemption-reversal-campaign.test.ts`
- Create: `kokoro-platform/test/integration/account-read-providers.test.ts`
- Create: `kokoro-platform/test/property/source-reversal.test.ts`

- [ ] Write RED tests for immutable `RedemptionRevocationFact`, source-exact Fulfillment reversal, unused term/Entitlement/Credit
reversal, consumed exposure to `RecoveryCase`, Code never returning to available, approved replacement with a new Batch/Code identity,
and resumable `RedemptionRevocationCampaign` cursor with per-item UoW/receipt and partial failure. Add owner-derived, Site-bound providers
for account products, credit summary, grant detail and usage detail; projections expose checkpoint/asOf/freshness and never invent zero
usage when evidence is missing. The migration owns only reversal/campaign/recovery/projection tables and constraints.
- [ ] Validate the default-Infra lease, then run RED separately:
  `pnpm -C kokoro-platform exec vitest run test/integration/redemption-reversal-campaign.test.ts test/property/source-reversal.test.ts`
- [ ] Run the independent read-provider RED even if the prior command failed:
  `pnpm -C kokoro-platform exec vitest run test/integration/account-read-providers.test.ts`
- [ ] Implement each reversal item as one `PlatformUnitOfWork` with command fence, source-specific output reversal, balanced Journal,
receipt/audit/outbox, and typed recovery. Implement the four generated-contract read operations plus preview/confirm/recovery/receipt
provider registration so the exact eight public resource groups are reachable and no extra Commerce route exists.
- [ ] Rerun focused tests, Prisma validation/generation, full Platform integration, typecheck and lint; commit Platform only:
```bash
git -C kokoro-platform add -- prisma/schema.prisma 'prisma/migrations/<timestamp>_wave_2a_reversal_campaign_reads/migration.sql' src/workflows/redemption-reversal/reverse-redemption.ts src/workflows/redemption-reversal/issue-replacement.ts src/workflows/redemption-reversal/run-batch-campaign.ts src/workflows/redemption-reversal/INDEX.md src/modules/commerce/application/account-read-service.ts src/modules/commerce/infrastructure/postgres/account-projection-repository.ts src/interfaces/http/commerce/account-routes.ts test/integration/redemption-reversal-campaign.test.ts test/integration/account-read-providers.test.ts test/property/source-reversal.test.ts
git -C kokoro-platform commit -m "feat(commerce): reverse sources and serve account projections"
```

At the Chunk 2 exit, run the Root `ga-check`, Platform `lease-check`, the complete Platform suite, migration-from-clean, migration-
from-Wave-1, and projection rebuild. Do not begin Admin/Web work if any schema owner or public resource group is incomplete.

## Chunk 3: Operations, Web, clean cut, and certification

### Platform Task P10: Add typed Admin and Support workflows

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/src/modules/commerce/application/admin-manifest.ts`
- Create: `kokoro-platform/src/workflows/admin-commerce/commands.ts`
- Create: `kokoro-platform/src/workflows/admin-commerce/INDEX.md`
- Create: `kokoro-platform/test/security/admin-commerce-scope.test.ts`
- Create: `kokoro-platform/test/integration/admin-commerce-command.test.ts`

- [ ] **Step 1: Write red tests** for publish/export/activate/reverse/AdminGrant/Journal correction maker-checker-executor separation,
step-up, canonical parameter digest, typed mutually exclusive scope, rejected-attempt receipt, Site non-disclosure, Support safe fields,
and Support safe fields. The tests must identify the missing policy/effect, not fail through test discovery.
- [ ] **Step 2: Run RED:** `pnpm -C kokoro-platform exec vitest run test/security/admin-commerce-scope.test.ts test/integration/admin-commerce-command.test.ts`
Expected: FAIL because the typed workflows are absent.
- [ ] **Step 3: Implement minimally** over Wave 1 Admin Connect command bus and the same Platform UoW; BreakGlass remains operation/resource/time bound and cannot enable Payment.
- [ ] **Step 4: Verify:** rerun focused tests plus Platform typecheck/lint/integration.
- [ ] **Step 5: Commit Platform only:**
```bash
git -C kokoro-platform add -- src/modules/commerce/application/admin-manifest.ts src/workflows/admin-commerce/commands.ts src/workflows/admin-commerce/INDEX.md test/security/admin-commerce-scope.test.ts test/integration/admin-commerce-command.test.ts
git -C kokoro-platform commit -m "feat(admin): operate commerce with typed controls"
```

### Web Task W2: Add generated-client-only Commerce Admin views

**Repository:** `kokoro-web`

**Depends on:** Platform P10 committed and its typed Wave 1 Admin command-bus manifest fixture published.

**Files:**
- Create: `kokoro-web/apps/admin/app/commerce/page.tsx`
- Create: `kokoro-web/apps/admin/app/redemption-cases/page.tsx`
- Create: `kokoro-web/apps/admin/lib/commerce/client.ts`
- Create: `kokoro-web/apps/admin/lib/commerce/client.test.ts`

- [ ] Write RED tests for generated-client-only access, typed scope and operation allowlists, safe Support fields, receipt recovery,
and absence of DB, arbitrary endpoint, generic CRUD, secret, Code plaintext or Payment access.
- [ ] Run `pnpm -C kokoro-web --filter @kokoro/admin-web exec vitest run lib/commerce/client.test.ts`; confirm a named missing client/view behavior.
- [ ] Implement server-only Admin Connect client/view adapters; run focused tests, Admin build, Web typecheck/lint and repository gates.
- [ ] Commit Web only:
```bash
git -C kokoro-web add -- apps/admin/app/commerce/page.tsx apps/admin/app/redemption-cases/page.tsx apps/admin/lib/commerce/client.ts apps/admin/lib/commerce/client.test.ts
git -C kokoro-web commit -m "feat(admin): add commerce operations views"
```

### Platform Task P11: Certify Platform-owned Payment surfaces with non-vacuous mutation gates

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/test/repository/payment-surfaces-closed.test.mjs`
- Create: `kokoro-platform/test/integration/payment-routes-disabled.test.ts`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/purchasable-catalog.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/payment-command.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/provider-worker-client.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/provider-secret-bootstrap.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/admin-payment-manifest.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/payment-schema-fact.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/payment-deployable.json`
- Create: `kokoro-platform/test/fixtures/payment-surface-mutations/provider-sdk-egress.json`

- [ ] Preserve the green Wave 1 Payment-closure baseline. Write mutation tests that inject one malicious fixture for each Platform-owned
surface: purchasable Offering/SalesPolicy, checkout/refund/webhook command, provider worker/client, Provider secret read/config bootstrap,
Admin Payment manifest/action, Payment schema/fact, deployable/process, and outbound SDK/egress. Each mutation must make the gate fail for
its intended reason; removing the fixture restores green.
- [ ] Run the static mutation-test RED and record its missing detector assertion:
  `pnpm -C kokoro-platform exec node --test test/repository/payment-surfaces-closed.test.mjs`
- [ ] Independently run the runtime RED even after static failure:
  `pnpm -C kokoro-platform exec vitest run test/integration/payment-routes-disabled.test.ts`
- [ ] Implement only fail-closed detector/admission regression gates. Legacy contracted probes either remain unregistered or return
stable `ACQUISITION_CHANNEL_DISABLED`, with zero Payment rows, provider egress, secret read and SDK initialization. Do not recreate or
“delete again” any Wave 1-removed Payment package/path.
- [ ] Rerun mutation tests, baseline Platform suite and deploy manifest scan; commit Platform only:
```bash
git -C kokoro-platform add -- test/repository/payment-surfaces-closed.test.mjs test/integration/payment-routes-disabled.test.ts test/fixtures/payment-surface-mutations/purchasable-catalog.json test/fixtures/payment-surface-mutations/payment-command.json test/fixtures/payment-surface-mutations/provider-worker-client.json test/fixtures/payment-surface-mutations/provider-secret-bootstrap.json test/fixtures/payment-surface-mutations/admin-payment-manifest.json test/fixtures/payment-surface-mutations/payment-schema-fact.json test/fixtures/payment-surface-mutations/payment-deployable.json test/fixtures/payment-surface-mutations/provider-sdk-egress.json
git -C kokoro-platform commit -m "test(platform): prevent payment surface regression"
```

### Web Task W3: Certify Web/Admin Payment surfaces with non-vacuous mutation gates

**Repository:** `kokoro-web`

**Depends on:** Platform P11 committed.

**Files:**
- Create: `kokoro-web/test/repository/payment-surfaces-closed.test.mjs`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/purchase-navigation.json`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/checkout-mock-refund-bff.json`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/arbitrary-commerce-proxy.json`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/admin-payment-surface.json`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/provider-secret-env.json`
- Create: `kokoro-web/test/fixtures/payment-surface-mutations/provider-sdk-init.json`

- [ ] Keep the Wave 1 baseline green. Inject malicious fixtures for purchase CTA/navigation, checkout/mock-pay/refund BFF, arbitrary
Commerce proxying, Admin Payment page/action/manifest, provider env/secret, and SDK initialization; prove each fixture independently
makes the scanner fail and removal restores green.
- [ ] Run `pnpm -C kokoro-web exec node --test test/repository/payment-surfaces-closed.test.mjs`; confirm RED on named missing mutation
detectors, not on already-absent Wave 1 files.
- [ ] Implement repository/runtime guards only, then run both app builds, Web repository/full suites, typecheck and lint.
- [ ] Commit Web only:
```bash
git -C kokoro-web add -- test/repository/payment-surfaces-closed.test.mjs test/fixtures/payment-surface-mutations/purchase-navigation.json test/fixtures/payment-surface-mutations/checkout-mock-refund-bff.json test/fixtures/payment-surface-mutations/arbitrary-commerce-proxy.json test/fixtures/payment-surface-mutations/admin-payment-surface.json test/fixtures/payment-surface-mutations/provider-secret-env.json test/fixtures/payment-surface-mutations/provider-sdk-init.json
git -C kokoro-web commit -m "test(web): prevent payment surface regression"
```

### Web Task W4: Build Site-bound Account and Redeem Web journeys

**Repository:** `kokoro-web`

**Files:**
- Create: `kokoro-web/apps/user/src/app/api/platform/redeem/preview/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/redeem/confirm/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/commands/[commandId]/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/redemptions/[redemptionId]/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/account/products/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/account/credits/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/account/credit-grants/[grantId]/route.ts`
- Create: `kokoro-web/apps/user/src/app/api/platform/account/usage/[usageId]/route.ts`
- Create: `kokoro-web/apps/user/src/platform/commerce-client.ts`
- Create: `kokoro-web/apps/user/src/platform/commerce-operation-allowlist.ts`
- Create: `kokoro-web/apps/user/src/ui/account/account-commerce.tsx`
- Create: `kokoro-web/apps/user/src/ui/redeem/redeem-form.tsx`
- Create: `kokoro-web/apps/user/tests/platform/commerce-client.test.ts`
- Create: `kokoro-web/apps/user/tests/ui/redeem-form.test.tsx`
- Create: `kokoro-web/apps/user/tests/e2e/redeem-account.spec.ts`

- [ ] **Step 1: Write red tests** for preview->confirm->lost-response receipt->Account, same-Plan stacking, Plan mismatch, safe generic
failure, no raw Code persistence/telemetry, Site/owner authority only from workload exchange/AuthSession, CSRF/idempotency, cross-Site
cookie/binding denial, projection freshness, and no checkout/Payment navigation. Add a repository/runtime test proving the eight
generated operations are the complete allowlist and that no catch-all/arbitrary-path proxy can be registered.
- [ ] **Step 2: Run red:** `pnpm -C kokoro-web --filter @kokoro/web-user exec vitest run tests/platform/commerce-client.test.ts tests/ui/redeem-form.test.tsx`
Expected: FAIL because generated-client BFF and views are absent.
- [ ] **Step 3: Implement minimally** with eight explicit handlers over the generated operation allowlist and a server-only generated
client. Browser submits Code only to the BFF and never supplies `siteId`, owner, BillingAccount, provider, raw Platform bearer or an
arbitrary downstream path. A generic `[...]` Commerce proxy is forbidden.
- [ ] **Step 4: Verify:** rerun focused tests, then `pnpm -C kokoro-web --filter @kokoro/web-user build` and the Playwright spec.
- [ ] **Step 5: Commit:**
```bash
git -C kokoro-web add -- apps/user/src/app/api/platform/redeem/preview/route.ts apps/user/src/app/api/platform/redeem/confirm/route.ts 'apps/user/src/app/api/platform/commands/[commandId]/route.ts' 'apps/user/src/app/api/platform/redemptions/[redemptionId]/route.ts' apps/user/src/app/api/platform/account/products/route.ts apps/user/src/app/api/platform/account/credits/route.ts 'apps/user/src/app/api/platform/account/credit-grants/[grantId]/route.ts' 'apps/user/src/app/api/platform/account/usage/[usageId]/route.ts' apps/user/src/platform/commerce-client.ts apps/user/src/platform/commerce-operation-allowlist.ts apps/user/src/ui/account/account-commerce.tsx apps/user/src/ui/redeem/redeem-form.tsx apps/user/tests/platform/commerce-client.test.ts apps/user/tests/ui/redeem-form.test.tsx apps/user/tests/e2e/redeem-account.spec.ts
git -C kokoro-web commit -m "feat(web): add redeem-only account journey"
```

### Platform Task P12: Perform the Platform clean replacement and produce child evidence

**Repository:** `kokoro-platform`

**Files:**
- Create: `kokoro-platform/scripts/migration/wave-2a-preflight.ts`
- Create: `kokoro-platform/scripts/migration/wave-2a-clean-cut.ts`
- Create: `kokoro-platform/scripts/migration/wave-2a-clean-cut-allowlist.json`
- Create: `kokoro-platform/scripts/migration/verify-wave-2a-clean-cut-allowlist.ts`
- Create: `kokoro-platform/test/migration/wave-2a-preflight.test.ts`
- Create: `kokoro-platform/test/migration/wave-2a-clean-cut.test.ts`
- Create: `kokoro-platform/test/migration/wave-2a-clean-cut-allowlist.test.ts`
- Create: `kokoro-platform/docs/evidence/wave-2a/platform-commerce-postgres.md`
- Create: `kokoro-platform/docs/evidence/wave-2a/code-export-delivery.md`
- Create: `kokoro-platform/docs/evidence/wave-2a/redeem-credit-conservation.md`
- Create: `kokoro-platform/docs/evidence/wave-2a/payment-surface-closure.md`

- [ ] **Step 1: Write red migration/certification tests** requiring an explicit clean-cut deletion allowlist whose exact paths and digest
are validated before mutation, no real external Payment receipt, no dual write/read, canonical
legacy inventory, clean install, double-Site seed, projection rebuild, reconciliation, backup/restore, Payment no-egress, contract mirror
parity, and exact GA SHA/wire hashes. Unexpected real Payment liability must hard-stop with immutable evidence.
- [ ] **Step 2: Validate the default-Infra lease, then run RED:**
  `pnpm -C kokoro-platform exec vitest run test/migration/wave-2a-preflight.test.ts test/migration/wave-2a-clean-cut.test.ts test/migration/wave-2a-clean-cut-allowlist.test.ts`
Expected: FAIL on named missing preflight/cutover behavior, never because PostgreSQL or tests are unavailable.
- [ ] **Step 3: Implement the one-shot Platform cutover**: validate the explicit deletion allowlist and reject any path/action outside
it before stopping old writes, then run preflight, migrate/seed through versioned commands,
verify counts/digests, switch to unified Platform and keep the legacy snapshot read-only. Never delete dev volumes/images or continue
if any receipt/reconciliation/Payment invariant is unknown. Root registry activation is not owned by this task.
- [ ] **Step 4: Run final Platform verification:**

Run: `pnpm -C kokoro-platform test && pnpm -C kokoro-platform test:integration && pnpm -C kokoro-platform typecheck && pnpm -C kokoro-platform lint`

Expected: PASS against clean and Wave 1 upgrade databases; all Platform test resources are released through the signed lease.

- [ ] **Step 5: Commit the final Platform SHA:**
```bash
git -C kokoro-platform add -- scripts/migration/wave-2a-preflight.ts scripts/migration/wave-2a-clean-cut.ts scripts/migration/wave-2a-clean-cut-allowlist.json scripts/migration/verify-wave-2a-clean-cut-allowlist.ts test/migration/wave-2a-preflight.test.ts test/migration/wave-2a-clean-cut.test.ts test/migration/wave-2a-clean-cut-allowlist.test.ts docs/evidence/wave-2a/platform-commerce-postgres.md docs/evidence/wave-2a/code-export-delivery.md docs/evidence/wave-2a/redeem-credit-conservation.md docs/evidence/wave-2a/payment-surface-closure.md
git -C kokoro-platform commit -m "test(platform): certify wave 2a clean cut"
```

Push this final child commit, wait for its independent remote CI, then create/push the unique annotated Platform release tag. No Root
pin may reference an earlier locally-green SHA.

### Root Task R3: Qualify compatibility/default Infra and atomically promote child pins

**Repository:** Root

**Depends on:** final Platform and Web commits pushed, independent child CI green, immutable artifacts/evidence available, and unique
annotated child tags pushed.

**Files:**
- Modify: `config/repository/compatibility-matrix.json`
- Modify: `config/repository/federated-repositories.json`
- Modify: `config/repository/bom.json`
- Modify: `config/repository/expected-snapshots.json`
- Modify: `config/repository/frozen-submodules.yaml`
- Modify: `contract/registry/boundaries.yaml`
- Modify: `scripts/architecture/check_ga_isolation.py`
- Create: `scripts/verification/wave-2a-qualification.mjs`
- Create: `scripts/verification/wave-2a-qualification.test.mjs`
- Create: `docs/reports/evidence/wave-2a/commerce-contract-runtime.md`
- Create: `docs/reports/evidence/wave-2a/redeem-code-export.md`
- Create: `docs/reports/evidence/wave-2a/credit-conservation-reconciliation.md`
- Create: `docs/reports/evidence/wave-2a/payment-surface-closure.md`
- Create: `docs/reports/evidence/wave-2a/web-redeem-account.md`
- Create: `docs/reports/evidence/wave-2a/migration-infra-promotion.md`
- Create: `docs/reports/evidence/wave-2a/ga-semantic-non-regression.md`
- Modify: `docs/task.md`
- Modify: `kokoro-platform`, `kokoro-web` gitlinks

- [ ] Write RED qualification modes: `--candidate` requires exact tagged child SHAs/artifact/report digests, real
provider/consumer compatibility, all eight public operations, Payment mutation evidence, default Infra inventory,
migration/rebuild/backup/restore, dual-Site isolation and the GA baseline; `--rollback-of` verifies restored pins/registry/matrices/BOM;
`--release` additionally requires final evidence documents and a BOM generated against the recorded candidate SHA. Missing
credentials/remote CI/evidence is blocking, never skipped.
- [ ] Run the Platform migration RED and Root GA RED as separate commands; expected failures must name missing Root qualification facts:
  `uv run --locked python -m pytest scripts/architecture/test_check_ga_isolation.py -q`
- [ ] Independently run `node --test scripts/verification/wave-2a-qualification.test.mjs` even if the Python command failed.
- [ ] As the sole Root integrator run guard `infra-inspect`; reconcile exactly one default stack only if required, acquire isolated
leases, verify no Payment process/credential/egress/default-app descriptor, execute compatibility and full Root/child gates, then release
leases and stop surplus verification containers through the Root manager. Preserve volumes/images/developer data and record final inventory.
- [ ] Atomically stage gitlinks, registry, matrices, expected/frozen snapshots, GA gate and qualification runner, then create
the local candidate promotion commit before any clone claim. Do not include final clone/rollback evidence that does not exist yet:

```bash
git add -- kokoro-platform kokoro-web contract/registry/boundaries.yaml config/repository/compatibility-matrix.json config/repository/federated-repositories.json config/repository/expected-snapshots.json config/repository/frozen-submodules.yaml scripts/architecture/check_ga_isolation.py scripts/verification/wave-2a-qualification.mjs scripts/verification/wave-2a-qualification.test.mjs
git commit -m "release(root): candidate wave 2a commerce closure"
wave2a_candidate_sha=$(git rev-parse HEAD)
```

- [ ] Verify that exact committed SHA in a recursive local clone, then use a second clone to create a new revert commit and rehearse
the previous pins/registry/matrices/BOM. A clone of an uncommitted worktree or uncommitted gitlink is forbidden:

```bash
wave2a_source_root=$(git rev-parse --show-toplevel)
wave2a_candidate_clone=$(mktemp -d)
wave2a_revert_clone=$(mktemp -d)
git clone --recurse-submodules "$wave2a_source_root" "$wave2a_candidate_clone/repo"
git -C "$wave2a_candidate_clone/repo" checkout --detach "$wave2a_candidate_sha"
git -C "$wave2a_candidate_clone/repo" submodule update --init --recursive
node "$wave2a_candidate_clone/repo/scripts/verification/wave-2a-qualification.mjs" --repo "$wave2a_candidate_clone/repo" --candidate "$wave2a_candidate_sha"
git clone --recurse-submodules "$wave2a_source_root" "$wave2a_revert_clone/repo"
git -C "$wave2a_revert_clone/repo" checkout --detach "$wave2a_candidate_sha"
git -C "$wave2a_revert_clone/repo" switch -c wave2a-rollback-rehearsal
git -C "$wave2a_revert_clone/repo" revert --no-edit "$wave2a_candidate_sha"
git -C "$wave2a_revert_clone/repo" submodule update --init --recursive
node "$wave2a_candidate_clone/repo/scripts/verification/wave-2a-qualification.mjs" --repo "$wave2a_revert_clone/repo" --rollback-of "$wave2a_candidate_sha"
```

Candidate mode regenerates both mirrors and runs clean install/migrate, compatibility and two-Site journeys against the exact commit.
Rollback mode verifies restored immutable refs and safe forward promotion. Any digest, receipt or reconciliation mismatch blocks.

- [ ] Persist sanitized candidate/revert SHAs and results, exact commands/counts, child artifacts, GA/Infra/migration/rebuild/
backup/restore/two-Site evidence. Generate and check the BOM only now that `wave2a_candidate_sha` exists, then create the follow-up
evidence/provenance commit. Remove only validated temporary clone directories:

```bash
node scripts/repository/generate-bom.mjs --promotion-commit "$wave2a_candidate_sha" --runtime-evidence .git/kokoro-wave2a/runtime-evidence.json
node scripts/repository/generate-bom.mjs --check --promotion-commit "$wave2a_candidate_sha"
git add -- docs/reports/evidence/wave-2a/commerce-contract-runtime.md docs/reports/evidence/wave-2a/redeem-code-export.md docs/reports/evidence/wave-2a/credit-conservation-reconciliation.md docs/reports/evidence/wave-2a/payment-surface-closure.md docs/reports/evidence/wave-2a/web-redeem-account.md docs/reports/evidence/wave-2a/migration-infra-promotion.md docs/reports/evidence/wave-2a/ga-semantic-non-regression.md docs/task.md config/repository/bom.json
git commit -m "docs(wave2a): record candidate and rollback evidence"
```

- [ ] Push the candidate plus follow-up evidence commits only after local review. Wait for remote Root CI to hydrate the exact child
tags/pins and pass `--release` on the follow-up commit. Only then create/push the Root BOM annotated tag; missing CI/credentials is a
blocker and an unverified Root commit is never tagged.

## Final release checklist

- [ ] Root public contract and both generated mirrors are byte-consistent; lifecycle becomes active only with real Platform/Web evidence.
- [ ] Every mutation claims/locks idempotency identity before business locks and uses the one Wave 1 UoW/security context.
- [ ] Fulfillment output line identity and Batch activation commitment are exact, durable, and replay-safe.
- [ ] One Credit authority owns Journal, root Hold, allocation stocks/cumulative flows, and AuthorizationSegment slices.
- [ ] Outbox/Inbox/DLQ validate canonical envelope digests; reconcilers never update authority tables directly.
- [ ] Typed Site/Global/BreakGlass scope remains mutually exclusive and fail-closed at the effect point.
- [ ] Payment acquisition is closed at all eight surfaces, including Admin, secrets, workers, deployables, and egress.
- [ ] Site Web Account/Redeem is Site-bound, generated-contract-driven, and never persists or logs raw Code.
- [ ] Clean replacement, double-Site isolation, backup/restore, rebuild/reconcile, and child/root CI evidence are complete.
- [ ] `kokoro-agent` SHA/tree and `run.request`/`run.cancel` wire bytes are unchanged.
