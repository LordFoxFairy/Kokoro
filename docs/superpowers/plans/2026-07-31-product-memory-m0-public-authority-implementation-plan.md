# Product Memory M0.1 Public Authority Implementation Plan

> **Execution:** use `superpowers:subagent-driven-development`; one worker owns one repository cut, and the Root owner reviews and verifies every commit from the canonical worktree.

**Goal:** ship the disabled-by-default, production-grade public authority for explicit personal Saved Memory: versioned CRUD, history/restore, priority, controls, import/export, immediate logical revoke and receipt-backed physical purge. This slice changes Root, Platform and Web, but not Session or GA runtime semantics.

**Architecture:** `kokoro-platform/src/modules/memory` is the only Product Memory authority. `platform-api` mounts the public operations through a dedicated `platform_memory_public` PostgreSQL credential. `platform-memory-worker` owns import quarantine and purge through `platform_memory_worker`. The future `platform-memory-runtime` login is qualified but has zero grants and no deployable until M2. Every external Site remains an independent Web project and opts into Memory through its signed Site release; browser requests never carry Site, subject, Project, namespace or database scope.

**Technology:** TypeScript 5.9 strict, Node.js 24, OpenAPI 3.1 + generated Zod/types, PostgreSQL 18, Node `crypto` AES-256-GCM, React/Next.js, Vitest, real PostgreSQL component tests, Playwright, Root compatibility/BOM gates.

**Authorities:** [PRD-19](../specs/2026-07-30-prd-19-product-memory-and-context-use.md), [ADR-013](../../kokoro-handbook/decisions/ADR-013-product-memory-and-context-authority.md), [codebase map](../../CODEBASE_MAP.md).

## 0. Scope and non-negotiable gates

M0.1 delivers only explicit personal Saved Memory and its user controls. Project Memory remains feature-off until its operation-specific membership/permission matrix and separate policy surface are frozen. `category = profile | preference | fact` describes content semantics only and never selects personal versus Project scope. The public settings response reports each independent axis as `{ requested, effective, availability, policyReason? }`:

- saved-memory use: `available`; user may change it;
- past-chat reference: `unavailable_until_session_m1a`; mutation is rejected;
- automatic learning: `unavailable_until_memory_m3`; mutation is rejected;
- Temporary Chat: absent, because Session is its owner.

M0.1 does **not** create `MemorySelectionSnapshot`, `context_assembly_receipt`, conversation search, embeddings, GA `MemoryPort`, automatic learning, Memory proposals, or per-response context-activity UI. Those claims remain No-Go until their owning phases are promoted.

The release flag stays disabled until all runtime assertions in Task 12 pass. A disabled Site has no route, nav entry, bootstrap claim or authorized BFF operation.

## 1. Target repository cuts

### Root authority

- Modify `contract/openapi/platform-public-v1.yaml`.
- Modify the existing `platform-public` entry in `contract/registry/boundaries.yaml`; do not add another boundary.
- Create `contract/tests/test_memory_public_contract.py`.
- Modify `contract/INDEX.md` and `docs/CODEBASE_MAP.md`.
- Do **not** modify `config/repository/compatibility-matrix.json` until Task 12.

### Platform authority

- Create `prisma/migrations/<timestamp>_memory_m0_public_authority/migration.sql`.
- Create `src/modules/memory/domain/memory-public.ts` and `memory-purge.ts`.
- Modify the existing `src/modules/memory/application/memory-authority-ports.ts`; do not create a second content-protection port.
- Create `src/modules/memory/application/memory-public-owner.ts` and `memory-purge-owner.ts`.
- Create `src/modules/memory/infrastructure/postgres-memory-public-repository.ts`, `postgres-memory-purge-repository.ts` and `memory-content-protector.ts`.
- Create `src/modules/memory/interfaces/http/memory-public-operations.ts`.
- Create `src/process/platform-memory-worker.ts` and `platform-memory-worker-composition.ts`.
- Modify `src/process/platform-api-runtime-contract.ts`, `platform-public-composition.ts`, `worker-deployment-contract.ts`, `deploy/docker/runtime-entrypoint.mjs`, `deploy/docker/Dockerfile`, `deployables.yaml`, `package.json`, module/process `INDEX.md` files and `docs/CODEBASE_MAP.md`.

### Web/Site product

- Create `packages/site-bff/src/memory-api.ts` and `packages/site-bff/test/memory-api.test.ts`.
- Create the full `packages/memory-app/` package following `packages/media-app/` conventions.
- Modify `packages/site-app-kit/src/index.ts`, `packages/site-scaffold/src/scaffold.ts`, `scripts/certify-external-sites.mjs`, `test/site/site-project-isolation.test.ts`, Root/Web indexes and `pnpm-lock.yaml`.
- Modify the independent Site template: `package.json`, `pnpm-workspace.yaml`, `next.config.ts`, `.env.example`, `deploy/artifact-manifest.json`, `scripts/verify-artifact.mjs`, `src/site-bootstrap.ts`, `src/bff.ts`, `src/app/memory/page.tsx`, and `src/app/api/memory/[[...path]]/route.ts`.

## 2. Chunk A — Root public contract

### Task 1: freeze complete public resources

**RED**

1. Create `contract/tests/test_memory_public_contract.py` using `test_media_public_contract.py` patterns.
2. Assert this closed operation set is present in `platform-public-v1.yaml`:

```python
MEMORY_OPERATIONS = {
    "getMemorySettings", "updateMemorySettings",
    "listMemoryEntries", "getMemoryEntry", "listMemoryEntryHistory",
    "rememberMemoryEntry", "correctMemoryEntry", "restoreMemoryEntryRevision",
    "prioritizeMemoryEntry", "deprioritizeMemoryEntry", "forgetMemoryEntry",
    "resetMemorySpace", "requestMemoryExport", "getMemoryExport",
    "requestMemoryImport", "getMemoryImport", "recoverMemoryCommand",
}
```

3. Assert request schemas reject `siteId`, `subjectRef`, `subjectGeneration`, `projectRef`, `spaceRef`, `namespace`, key bytes, raw source credentials and caller-supplied digests.
4. Assert text is at most 16 KiB UTF-8; import manifests and command bodies are at most 64 KiB; cursor is at most 2048 bytes; list limit is 1–100; every object is closed.
5. Assert history is immutable, restore creates a new revision, forget/reset return `revoked_purge_pending | purged`, and async import/export expose typed status plus command recovery.
6. Run:

```bash
uv run pytest contract/tests/test_memory_public_contract.py -q
```

Expected: RED because Memory paths do not exist.

**IMPLEMENT**

7. Add resources under `/v1/memory/settings`, `/v1/memory/entries`, `/v1/memory/entries/{entryRef}/history`, `/v1/memory/exports/{exportRef}`, `/v1/memory/imports/{importRef}` and `/v1/memory/commands/{commandId}`.
8. Bind mutating commands to the existing authenticated command/idempotency header convention. `restore`, `priority`, `forget`, `reset`, `import` and `export` are explicit operations, not a generic action endpoint.
9. Model import as an Asset-owned quarantined upload reference plus digest/format; Memory never accepts raw multipart bytes. Model export delivery as a short-lived Artifact-owned download handle; the status object never carries ciphertext or a permanent URL.
10. Extend the existing `platform-public` operation list in `contract/registry/boundaries.yaml`; keep lifecycle `contract-only` and keep it absent from the compatibility matrix.
11. Generate into a temporary directory to prove determinism without mutating child repos:

```bash
memory_tmp="$(mktemp -d)"
node contract/generate-public-openapi.mjs --schema platform-public-v1 --output "$memory_tmp/platform-public"
test -s "$memory_tmp/platform-public/operations.gen.ts"
```

12. Run:

```bash
uv run pytest contract/tests/test_memory_public_contract.py contract/tests/test_media_public_contract.py -q
node scripts/contract/check-boundary-registry.mjs
git diff --check
```

13. Update `contract/INDEX.md` and `docs/CODEBASE_MAP.md`; commit only Root-owned files:

```bash
git commit -m "feat(contract): publish product memory public API"
```

### Task 2: promote generated mirrors independently

1. From Root, run `node contract/generate-public-openapi.mjs --schema platform-public-v1`. The only generated changes must be:
   - `kokoro-platform/src/interfaces/http/generated/platform-public/**`
   - `kokoro-web/packages/site-client/src/generated/platform-public/**`
2. In Platform, run `pnpm typecheck:platform` and generated metadata tests, then commit only the Platform mirror as `chore(contract): promote memory public mirror`.
3. In Web, run `pnpm --filter @kokoro/site-client typecheck` and package tests, then commit only the Web mirror with the same subject.
4. Re-run the generator and require zero diff in both child repositories.

## 3. Chunk B — Platform database and cryptographic authority

### Task 3: split immutable headers from erasable content

**RED**

1. Create `test/architecture/memory-m0-public-schema.test.ts` for static migration invariants.
2. Extend `test/component/postgres-foundation.test.ts` with a focused `memory public role authority` case using real PostgreSQL.
3. Prove three actual roles are `LOGIN NOINHERIT NOBYPASSRLS`, own no database/schema/relation/sequence/routine/type objects, have no memberships, cannot `SET ROLE`, have no database `CREATE`/`TEMP`, cannot create/use objects in `public`, and fail on an exact pinned-OID mismatch. The test must never rename, drop or recreate a canonical cluster role.
4. Prove public/runtime/worker cannot read tables directly, PUBLIC has no execute, neighboring roles cannot call Memory routines, arbitrary GUC injection grants nothing, and wrong Site/subject generation/Project membership/authorization epoch returns no fact.
5. Run the focused tests; expect RED.

**IMPLEMENT**

6. In the forward migration, keep `platform.memory_revision` as immutable content-free header. Move `protected_ciphertext`, key revision and envelope metadata into a new erasable `platform.memory_revision_payload` keyed by the full `(site_ref, space_ref, entry_ref, revision, revision_ref)` identity.
7. Add append-only `memory_public_command_inbox`, `memory_import_job`, `memory_export_job`, `memory_purge_job`, `memory_purge_participant_receipt` and content-free suppression tombstone tables. Do not add lexical, selection or ContextAssembly tables.
8. Define a versioned participant manifest covering revision payload, public presentation cache, import quarantine object, export object, command/outbox payload and backup/object-GC acknowledgement. M1a/M2/M3 participants are recorded as policy-versioned `not_applicable`, never silently skipped.
9. Replace the old immutable trigger only as needed to permit deletion of payload rows; immutable revision headers, provenance and receipt identities remain update/delete protected.
10. Keep the feature-off database surface closed. Internal owner-authority helpers use fixed `search_path = pg_catalog, platform`, but no generic `authorize_read` / `authorize_command` routine is granted to a runtime role. The operation-specific owner read/write routines and their grants land atomically in Task 5; do not create a reusable authorization oracle or trust caller-set GUCs.
11. Add the three credential classes to the central migrator preflight, distinct-role set, ownership inventory, postflight and pinned-OID authority. `platform_memory_public` and `platform_memory_runtime` receive zero execute/table grants until their owning composition lands; `platform_memory_worker` receives only the exact purge routines already exercised in this task.
12. Build and apply all migrations to a uniquely named temporary database using the existing Postgres service:

```bash
pnpm build:runtime
node dist/src/infrastructure/postgres/migrator.js
pnpm test:component:postgres -- -t "memory public role authority"
```

The verification helper creates and removes a uniquely named temporary database while treating the canonical cluster roles as immutable inputs. OID-drift tests mutate only transactional authority facts and roll them back. Before/after role OIDs, attributes, memberships, ownership, ACLs and default Infra inventory must be identical.
13. Run the static schema test and commit `feat(memory): separate public authority and erasable payloads`.

### Task 4: implement one exact content-protection envelope

**RED**

1. Create `test/unit/memory-content-protector.test.ts`.
2. Cover AES-256-GCM only: 32-byte keys, 12-byte random nonce, 16-byte tag, envelope version, key revision, ciphertext bound and AAD mismatch for every axis.
3. Cover key rotation, unknown/retired key, copied input/output buffers, no plaintext in error objects and no default/dev key in production.

**IMPLEMENT**

4. Extend `MemoryContentProtectionPort` to support `protect` and `reveal` with exact binding:

```ts
type MemoryPayloadBinding = Readonly<{
  siteRef: SiteRef;
  spaceRef: MemorySpaceRef;
  entryRef: MemoryEntryRef;
  revisionRef: MemoryRevisionRef;
}>;

interface MemoryContentProtectionPort {
  protect(input: Readonly<{ binding: MemoryPayloadBinding; plaintext: Uint8Array }>): Promise<ProtectedMemoryContent>;
  reveal(input: Readonly<{ binding: MemoryPayloadBinding; protectedContent: ProtectedMemoryContent }>): Promise<Uint8Array>;
}
```

5. Canonical AAD is `kokoro.memory.payload.v1\0` plus length-framed UTF-8 axes. Persist `version | keyRevision | nonce | ciphertext | tag | aadDigest`; compare AAD digest before decrypting.
6. Load a bounded key-ring JSON from a private file through `platform-api-runtime-contract.ts`; validate ownership/mode/trust-root using existing secret-file helpers.
7. Run focused unit tests, `pnpm lint`, and `pnpm typecheck:platform`; commit `feat(memory): protect revision payloads with bound envelopes`.

## 4. Chunk C — Platform application and process closure

### Task 5: implement public owner, history and bounded list reads

1. Create RED tests:
   - `test/unit/memory-public-owner.test.ts`
   - `test/unit/memory-public-read-owner.test.ts`
   - `test/unit/memory-postgres-public-repository.test.ts`
2. Cover current authority revalidation, keep-first command replay/conflict, correction CAS, restore-as-new-revision, stable priority ordering, owner snapshot/cursor binding, not-found/access collapse, revoked/purged states and response byte/item caps.
3. Implement `MemoryPublicOwner` by orchestrating the existing `MemoryAuthorityService`; do not duplicate remember/correct/forget/reset rules.
4. Public list reads support only exact category/source/state filters and stable keyset pagination over active explicit entries. The first list or revision-history page returns an opaque `snapshotRef + spaceVersion`; every continuation cursor binds scope, normalized filters, ordering and that exact pair. Any mutation that changes public entry content/head, priority, active membership, forget or reset state advances `spaceVersion`; an old list or history continuation fails stale. Succeeded commands replay their exact committed version and detail reads expose the observed version. Content FTS/trigram and relevance ranking remain M1a; M0.1 creates no search index or `MemorySelectionSnapshot`.
5. Apply server-owned content admission before protection or persistence. M0.1 accepts only ordinary explicit facts/preferences; secret material and protected/special-category content fail closed as `policy_rejected`. A browser boolean or client classification is never sufficient. The explicit protected-category confirmation workflow remains M3 and must arrive with its own versioned challenge/receipt contract.
6. Install exact operation-specific `SECURITY DEFINER` read/write routines with fixed `search_path`, exact `session_user` name/OID, current Site/subject/Project/feature-policy revalidation and closed result shapes. Grant only those routines to `platform_memory_public`; the generic authorization helpers remain inaccessible.
7. Repositories receive only the dedicated Memory-public client and call those authority routines; no public code imports migrator/admin clients or performs cross-module table joins.
8. Run focused tests, lint and typecheck; commit `feat(memory): add explicit public owner and search`.

### Task 6: make import/export and purge recoverable

1. Create RED tests:
   - `test/unit/memory-purge-owner.test.ts`
   - `test/unit/memory-import-export-owner.test.ts`
   - `test/unit/memory-worker-composition.test.ts`
2. Cover forget/reset racing with bounded list reads, worker lease takeover, response loss, repeated participant receipts, stale watermark, quarantined invalid import, export expiration, object-store cleanup and versioned `not_applicable` participants.
3. The logical-revoke transaction advances use/revocation generation and appends purge job/outbox before returning. No new read/search can see the entry after commit.
4. Purge removes every M0.1 content/derived participant through a frozen cutoff. Completion requires all applicable receipts; until then public state is `revoked_purge_pending`.
5. Import validates an exported Kokoro manifest, Site policy, schema version, size/digest and category; imported entries create ordinary revisions with `source_kind=import`. It never restores a purged revision identity.
6. Export freezes a cutoff and produces a versioned encrypted artifact; status and delivery use opaque refs and current authorization. Every import/export aggregate starts `statusVersion` at one and increments it on every persisted public status change; reducers discard lower versions and require byte-equivalent replay at the same version. State transitions follow the closed contract graph and cannot regress. A completed import publishes the exact `resultingSpaceVersion` from its apply transaction; every non-completed import status carries null.
7. Implement `platform-memory-worker-composition.ts` with production adapters only and `platform-memory-worker.ts` using `hostPlatformWorkerProcess`.
8. Add `platform-memory-worker` to `worker-deployment-contract.ts`, `runtime-entrypoint.mjs`, `Dockerfile`, `deployables.yaml` and `package.json` (`start:memory-worker`). Include exact DB role, worker id, key-ring, Asset/Artifact endpoints and TLS/file contracts.
9. Keep the worker deployable `activationAuthorized: false` until Task 12.
10. Run focused tests and commit `feat(memory): make import export and purge recoverable`.

### Task 7: mount public HTTP through its own credential

1. Create RED tests:
   - `test/unit/memory-public-http.test.ts`
   - extend `test/unit/platform-api-runtime-contract.test.ts`
   - extend `test/architecture/deployable-roles.test.ts`
2. Add separately validated `DATABASE_URL_PLATFORM_MEMORY_PUBLIC`, expected role and expected role OID inputs. Construct a dedicated client and prove `session_user`/OID before readiness.
3. Implement exact generated operation handlers in `memory-public-operations.ts`; unknown operation IDs fail closed. Map typed 409/202/recovery states without exposing existence.
4. Inject only the dedicated Memory client, protector, cursor and Asset/Artifact ports into the Memory composition inside `platform-public-composition.ts`.
5. Update Memory and Platform `INDEX.md` files.
6. Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
```

7. Commit `feat(memory): mount isolated public memory operations`.

## 5. Chunk D — Web and independent Site closure

### Task 8: implement the Site BFF façade

1. Create `packages/site-bff/test/memory-api.test.ts` before implementation.
2. Cover exact paths/methods, same-origin, CSRF for mutations, duplicate query rejection, 64 KiB request cap, invalid UTF-8, one monotonic 30-second auth+context+upstream budget, abort propagation, response cap and typed outcome-unknown recovery.
3. Implement `packages/site-bff/src/memory-api.ts`; derive Site/actor/Project context from verified auth and product bootstrap. Never proxy arbitrary paths or accept scope identifiers from the browser.
4. Export only the typed façade from `packages/site-bff/src/index.ts` and update its `INDEX.md`.
5. Run package tests/typecheck/lint; commit `feat(memory): add Site BFF façade`.

### Task 9: build the Memory product package

1. Create exact package files: `package.json`, `INDEX.md`, `eslint.config.mjs`, `tsconfig.json`, `tsconfig.build.json`, `vitest.config.ts`, `src/index.ts`, `src/memory-controller.ts`, `src/memory-product.tsx`, `src/memory-product.module.css`, `src/css.d.ts`, `test/memory-controller.test.ts`, `test/memory-product.test.tsx`.
2. RED tests cover snapshot-bound cursor pagination, legal first-page omission after a command, stale continuation recovery, bounded scope-level owner-version fencing, A→B deep-link stale clearing, monotonic revision merge, command journal/recovery, restore conflict, purge pending, priority, import/export reducer races, destructive confirmation, keyboard/focus/screen-reader status and reduced motion.
3. Implement separate requested/effective/availability controls. Unavailable past-chat/automatic-learning axes are explanatory and cannot send mutation commands.
4. Render text/typed fields only; never raw HTML. In M0.1, server policy rejects protected/special-category content because the confirmation challenge contract does not yet exist; Web must not guess sensitivity or invent a boolean acknowledgement. Render only the contract's safe source label/state. A clickable source is forbidden until M1a provides an opaque, current-Site reauthorization action; raw Session/Asset/provider identifiers are never turned into links.
5. Run package gates and commit `feat(memory): add saved-memory controls`.

### Task 10: include Memory in the independently deployable Site artifact

1. Extend `test/site/site-project-isolation.test.ts` first. Generate two Sites: one Memory-enabled, one disabled.
2. Modify `packages/site-scaffold/src/scaffold.ts` and the template files listed in section 1. Add the Memory page and exact catch-all BFF route, package dependency, transpilation allowlist, runtime configuration, feature bootstrap and artifact manifest entries.
3. Extend `scripts/certify-external-sites.mjs` and template `scripts/verify-artifact.mjs` so missing or unexpected Memory files/dependencies fail certification.
4. Memory-disabled output must have no page, route, nav, bootstrap claim or authorized upstream operation. Backend capability alone never exposes the product.
5. Build both generated Site projects in clean temporary directories; verify their artifacts independently.
6. Run Web full gates and commit `feat(memory): bind saved memory to Site artifacts`.

## 6. Chunk E — runtime evidence and promotion

### Task 11: real database, security and browser journeys

1. Start/reuse only services named by `config/repository/compatibility-matrix.json#runtimeGate.requiredServices`; do not hard-code a container count and do not create business containers.
2. Run the real PostgreSQL role/OID/RLS suite from Task 3.
3. Launch Platform and two generated Site projects as bounded host processes.
4. Exercise: remember with lost response and recovery; list/get/history; correct; restore; priority; pause use; invalid and valid import; export status/delivery; forget with immediate invisibility; purge completion; reset; disabled Site; cross-Site and neighboring-role denials.
5. Add `scripts/compatibility/platform-web-memory-public.mjs` and its test. Evidence must include real provider and official generated Site BFF calls, generated contract digests, role OIDs and child SHAs; mocks are insufficient.
6. Stop host processes and require the default Infra inventory to match its authority file exactly.

### Task 12: activate compatibility and atomically promote pins

1. Only after Task 11 passes, add `platform-public@v1` to `config/repository/compatibility-matrix.json` and matching provider/consumer roles to both child entries in `config/repository/federated-repositories.json`.
2. Run clean-worktree full gates for Platform and Web; run Root contract/repository/compatibility suites and generated-mirror zero-diff.
3. Push each independent child branch, wait for green remote CI, and create unique annotated tags. Record tag object and peeled commit SHA.
4. Update Root gitlinks, `config/repository/bom.json`, `docs/task.md`, `docs/CODEBASE_MAP.md` and `docs/reports/evidence/wave-0/product-memory-m0-public-certification.md` in one promotion commit.
5. Clone Root recursively into a clean temporary directory, regenerate contracts, build two independent Sites and rerun compatibility.
6. Rehearse rollback to the previous four-repository BOM. Disabled release must remove all Memory product routes without deleting authority data.
7. Root BOM tag is forbidden until Root remote CI is green with its required submodule credential.

## 7. Required successor plans

- **M1a:** Platform cited FTS/trigram `MemorySelectionSnapshot`, Session cited conversation search/source resolver, Temporary Chat enforcement and source deletion flow. This is a Root/Platform/Session/Web promotion.
- **M1b:** Root-qualified pgvector PostgreSQL image, exact policy-prefiltered semantic search, shadow reindex and rollback.
- **M2:** Admission `RunContextManifest`, GA `MemoryPort`, journaled dynamic searches, GA `ContextAssemblyReceipt`, Session `ContextActivityProjection`, and Web per-response source activity. Agent core notice and review are mandatory before implementation.
- **M3:** conversation-source learning feed, proposal/confirmation, extraction/consolidation and sensitive-category policies.

No successor phase may reuse M0.1 UI labels to imply unavailable runtime behavior.
