# Contract Foundation and Admin Auth Connect Pilot Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the generated ConnectRPC/Buf contract foundation, migrate Admin Auth off hand-written HTTP and Web-owned Prisma access, and give Session one explicit Platform admission boundary without changing GA behavior.

**Architecture:** Root owns protobuf sources, generation configuration, contract digests and federated compatibility evidence. Platform implements the generated privileged Admin Auth service on its existing Fastify role; Admin Web consumes it through a server-only generated client and deletes all Platform database access. Session introduces a narrow `PlatformAdmissionPort` around existing behavior so later `PrepareRun/FinalizeRun/Receipt` Connect migration replaces one adapter instead of preserving scattered Model/Credit/Hub clients.

**Tech Stack:** Node 22, TypeScript 5.9, pnpm 11.2.2, Buf 1.72.0, Protobuf-ES 2.13.0, ConnectRPC 2.1.2, `@connectrpc/validate` 0.2.0, Fastify 5, Prisma 6.19.3, Next.js 16.2.6, Auth.js 5 beta, Vitest, Python root contract checks.

**Authoritative spec:** `docs/superpowers/specs/2026-07-27-contract-transport-and-internal-rpc-design.md`

**Hard boundaries:** No GA source changes. No sibling source imports. No Web access to Platform DB. No new hand-written RPC URL/schema/version/error layer. Do not convert Platform-local workflows to Connect. Preserve all existing public HTTP/SSE behavior.

---

## File Structure

### Root-owned contract and federation files

- `contract/package.json`: pinned Buf and Protobuf-ES generation toolchain only.
- `contract/pnpm-lock.yaml`: exact root contract-tool dependencies.
- `contract/buf.yaml`: module, Protovalidate dependency, STANDARD lint and FILE breaking policy.
- `contract/buf.lock`: exact protobuf dependency commit.
- `contract/buf.gen.yaml`: deterministic TypeScript generation into checked-in Platform/Web mirrors.
- `contract/proto/kokoro/common/v1/error.proto`: typed safe error and retry classification.
- `contract/proto/kokoro/common/v1/receipt.proto`: command identity and receipt state.
- `contract/proto/kokoro/platform/admin/v1/admin_auth.proto`: Admin Auth service and messages.
- `contract/tests/test_buf_contract.py`: source/layout/version/dependency invariants.
- `scripts/repository/check-generated-contracts.mjs`: byte/diff gate for generated mirrors.
- `scripts/repository/check-generated-contracts.test.mjs`: command and failure tests.
- `scripts/compatibility/admin-auth-connect.mjs`: live generated-client/provider scenario.
- `scripts/compatibility/admin-auth-connect.test.mjs`: closed machine-result and cleanup tests.
- `config/repository/federated-repositories.json`: provider/consumer protocol declarations.
- `config/repository/compatibility-matrix.json`: required Admin Auth scenario.
- `.github/workflows/contract.yml`: install pinned contract tools and execute Buf gates.
- `contract/README.md`, `docs/CODEBASE_MAP.md`, `docs/CURRENT.md`: authoritative entry-point updates.

### Platform-owned provider files

- `kokoro-platform/kokoro-platform-admin/src/generated/contracts/**`: generated protobuf/service descriptors; never hand-edit.
- `kokoro-platform/kokoro-platform-kit/src/rpc/workload-auth.ts`: temporary legacy-secret-compatible workload interceptor.
- `kokoro-platform/kokoro-platform-kit/src/rpc/errors.ts`: Connect code and safe error-detail mapping.
- `kokoro-platform/kokoro-platform-kit/src/rpc/INDEX.md`: public exports and transport constraints.
- `kokoro-platform/kokoro-platform-admin/src/admin-auth-service.ts`: application-facing Connect implementation.
- `kokoro-platform/kokoro-platform-admin/src/admin-auth-store.ts`: Platform-owned persistence port/Prisma adapter.
- `kokoro-platform/kokoro-platform-admin/src/admin-auth-receipt.ts`: command idempotency and receipt transaction.
- `kokoro-platform/kokoro-platform-admin/prisma/schema.prisma`: Admin Auth receipt model if no equivalent existing owner receipt exists.
- `kokoro-platform/kokoro-platform-admin/prisma/migrations/<timestamp>_admin_auth_receipts/migration.sql`: additive receipt migration.
- `kokoro-platform/kokoro-platform-admin/src/server.ts`: register generated Connect routes/interceptors.
- `kokoro-platform/kokoro-platform-admin/src/main.ts`: compose store and service.
- `kokoro-platform/kokoro-platform-admin/test/unit/admin-auth-service.test.ts`: handler/error/auth tests.
- `kokoro-platform/kokoro-platform-admin/test/integration/admin-auth-connect.test.ts`: real Fastify/Connect/DB lifecycle.
- Delete the uncommitted hand-written `src/admin-auth-rpc.ts` and its transport-specific tests after equivalent generated tests are green.

### Web-owned consumer files

- `kokoro-web/apps/admin/lib/generated/contracts/**`: generated protobuf/service descriptors; never hand-edit.
- `kokoro-web/apps/admin/lib/auth/client.ts`: server-only Connect client implementing the Auth.js-facing port.
- `kokoro-web/apps/admin/lib/auth/adapter.ts`: Auth.js adapter depending only on `AdminAuthClient`.
- `kokoro-web/apps/admin/lib/auth/events.ts`: generated client call; no Prisma import.
- `kokoro-web/apps/admin/auth.ts`: construct/inject one server client and remove direct operator query.
- `kokoro-web/apps/admin/lib/env.ts`: no `DATABASE_URL_ADMIN`; retain gateway URL and temporary proxy secret.
- `kokoro-web/apps/admin/README.md` and nearest `INDEX.md`: owner, generated client and server-only constraints.
- Delete `kokoro-web/apps/admin/lib/prisma.ts` and `kokoro-web/apps/admin/prisma/schema.prisma`.
- Remove `@auth/prisma-adapter`, `@prisma/client`, `prisma`, Prisma scripts and generated artifacts from Web.

### Session-owned boundary files

- `kokoro-session/src/platform/admission-port.ts`: target application contract independent of HTTP/Connect.
- `kokoro-session/src/platform/legacy-admission-adapter.ts`: explicit transition adapter composing existing Model/Credit/Hub clients.
- `kokoro-session/src/platform/INDEX.md`: ownership, target deletion path and GA prohibition.
- `kokoro-session/src/main.ts`: one injected `PlatformAdmissionPort` composition point.
- `kokoro-session/tests/platform-admission-port.test.ts`: behavior and dependency-direction tests.
- No generated Admission Connect client in this pilot; its proto and provider workflow belong to the next Platform Admission plan.

---

## Chunk 1: Root Contract Foundation

### Task 1: Pin the standard contract toolchain

**Files:**

- Create: `contract/package.json`
- Create: `contract/pnpm-lock.yaml`
- Create: `contract/buf.yaml`
- Create: `contract/buf.gen.yaml`
- Create: `contract/tests/test_buf_contract.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing root contract-layout test**

Add assertions that:

```python
def test_buf_contract_toolchain_is_exact_and_local() -> None:
    package = json.loads((ROOT / "contract/package.json").read_text())
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protobuf": "2.13.0",
        "@bufbuild/protoc-gen-es": "2.13.0",
    }


def test_buf_policy_is_standard_and_file_strict() -> None:
    config = yaml.safe_load((ROOT / "contract/buf.yaml").read_text())
    assert config["lint"]["use"] == ["STANDARD"]
    assert config["breaking"]["use"] == ["FILE"]
```

- [ ] **Step 2: Run the test and prove RED**

Run: `uv run pytest contract/tests/test_buf_contract.py -q`

Expected: FAIL because `contract/package.json` and Buf configs do not exist.

- [ ] **Step 3: Add exact package/config files**

Use a private package with scripts `buf:format`, `buf:lint`, `buf:generate`, and `buf:breaking`. Configure the module path as `proto`, dependency `buf.build/bufbuild/protovalidate`, STANDARD lint and FILE breaking. Configure `protoc-gen-es` with `target=ts` and `import_extension=js`; generate identical descriptors into the Platform Admin and Admin Web generated roots.

- [ ] **Step 4: Install once and commit the exact lock**

Run: `pnpm --dir contract install`

Expected: `contract/pnpm-lock.yaml` created; no root or child lock changes.

- [ ] **Step 5: Prove GREEN and execute the pinned CLI**

Run:

```bash
uv run pytest contract/tests/test_buf_contract.py -q
pnpm --dir contract exec buf --version
```

Expected: tests PASS and Buf reports `1.72.0`. Buf lint begins in Task 2 after the first real proto exists; an empty Buf module correctly fails lint and must not be hidden with a placeholder schema.

- [ ] **Step 6: Commit**

```bash
git add contract/package.json contract/pnpm-lock.yaml contract/buf.yaml contract/buf.gen.yaml contract/tests/test_buf_contract.py .gitignore
git commit -m "build(contract): pin protobuf toolchain"
```

### Task 2: Define common errors, receipts and Admin Auth v1

**Files:**

- Create: `contract/proto/kokoro/common/v1/error.proto`
- Create: `contract/proto/kokoro/common/v1/receipt.proto`
- Create: `contract/proto/kokoro/platform/admin/v1/admin_auth.proto`
- Modify: `contract/tests/test_buf_contract.py`

- [ ] **Step 1: Add failing schema-policy tests**

Assert package names end in `.v1`, service methods are exactly:

```text
GetOperatorByEmail
GetOperator
CreateVerificationToken
ConsumeVerificationToken
RecordAuthEvent
GetCommandReceipt
```

Assert effect requests carry non-empty `command_id`, `idempotency_key` and `request_digest`; email/token strings have Protovalidate bounds; timestamps use `google.protobuf.Timestamp`; no raw secret appears in an error/receipt message.

- [ ] **Step 2: Run RED**

Run: `uv run pytest contract/tests/test_buf_contract.py -q`

Expected: FAIL because proto files are absent.

- [ ] **Step 3: Add the proto contracts**

Define closed enums for operator status, retry class, receipt state and auth-event kind. Use typed request/response messages rather than generic maps. `GetOperatorByEmail` uses a POST-style unary body through Connect, so email never enters a URL. `GetCommandReceipt` returns owner-authoritative state plus safe response metadata; it never returns a verification token.

- [ ] **Step 4: Format, lint and generate**

Run:

```bash
pnpm --dir contract run buf:format
pnpm --dir contract run buf:lint
pnpm --dir contract run buf:generate
```

Expected: generated TypeScript appears only in the two configured child mirror directories.

- [ ] **Step 5: Prove deterministic generation**

Run generation twice, then `git diff --exit-code` against generated directories after staging the intended first output.

Expected: second generation creates no diff.

- [ ] **Step 6: Run tests and commit root schema separately**

Run: `uv run pytest contract/tests -q`

Commit root schema/config first; child generated mirrors are committed by their owners, then root records their exact pins.

### Task 3: Add generated-contract and breaking gates

**Files:**

- Create: `scripts/repository/check-generated-contracts.mjs`
- Create: `scripts/repository/check-generated-contracts.test.mjs`
- Modify: `.github/workflows/contract.yml`
- Modify: `contract/README.md`
- Modify: `scripts/repository/INDEX.md`

- [ ] **Step 1: Write failing Node tests**

Cover clean generation, changed generated file, missing mirror, generator non-zero exit, timeout and sanitized diagnostics. The checker must not print environment variables or file contents.

- [ ] **Step 2: Run RED**

Run: `node --test scripts/repository/check-generated-contracts.test.mjs`

- [ ] **Step 3: Implement the checker**

Run pinned `pnpm --dir contract run buf:generate`, then inspect only declared generated paths with `git diff --exit-code`. Return structured codes such as `generated_contract_drift`, never silently rewrite during check mode.

- [ ] **Step 4: Wire CI**

Add `pnpm --dir contract install --frozen-lockfile`, Buf format/lint, generated diff and `buf breaking` against the PR base/root main contract. Keep existing Python mirror checks.

- [ ] **Step 5: Verify and commit**

Run:

```bash
node --test scripts/repository/check-generated-contracts.test.mjs
uv run pytest contract/tests -q
node scripts/repository/check-generated-contracts.mjs
```

Expected: all PASS and a clean generated diff.

---

## Chunk 2: Platform Admin Connect Provider

### Task 4: Add Platform Connect dependencies and generated exports

**Files:**

- Modify: `kokoro-platform/kokoro-platform-admin/package.json`
- Modify: `kokoro-platform/kokoro-platform-kit/package.json`
- Modify: `kokoro-platform/pnpm-lock.yaml`
- Create: `kokoro-platform/kokoro-platform-kit/src/rpc/INDEX.md`
- Modify: `kokoro-platform/kokoro-platform-kit/src/index.ts`
- Generated: `kokoro-platform/kokoro-platform-admin/src/generated/contracts/**`

- [ ] **Step 1: Add a failing generated-service import test**

The test imports `AdminAuthService` from the generated mirror and asserts all six method descriptors exist. It must not import from root or Web.

- [ ] **Step 2: Run RED**

Run: `pnpm --dir kokoro-platform --filter @kokoro/platform-admin test`

- [ ] **Step 3: Add exact runtime dependencies**

Use exact `@connectrpc/connect@2.1.2`, `@connectrpc/connect-node@2.1.2`, `@connectrpc/connect-fastify@2.1.2`, `@connectrpc/validate@0.2.0`, `@bufbuild/protobuf@2.13.0`, and `@bufbuild/protovalidate@1.2.0` only where needed. Do not add `protoc-gen-connect-es`; Protobuf-ES v2 generates service descriptors.

- [ ] **Step 4: Generate and run GREEN**

Run root generation, then Platform Admin tests/typecheck.

- [ ] **Step 5: Commit the dependency/generated slice in `kokoro-platform`**

Commit only manifest, lock, generated files and import test.

### Task 5: Implement centralized workload/auth/error interceptors

**Files:**

- Create: `kokoro-platform/kokoro-platform-kit/src/rpc/workload-auth.ts`
- Create: `kokoro-platform/kokoro-platform-kit/src/rpc/errors.ts`
- Create: `kokoro-platform/kokoro-platform-kit/test/rpc-workload-auth.test.ts`
- Create: `kokoro-platform/kokoro-platform-kit/test/rpc-errors.test.ts`
- Modify: `kokoro-platform/kokoro-platform-kit/src/index.ts`
- Modify: `kokoro-platform/kokoro-platform-kit/src/rpc/INDEX.md`

- [ ] **Step 1: Write RED tests**

Cover missing caller, wrong audience, wrong secret, current/previous rotation secrets, expired deadline, safe error details and secret/PII absence. The temporary legacy metadata is accepted only inside the interceptor and converted to a typed workload context.

- [ ] **Step 2: Implement minimal interceptors**

Use constant-time secret comparison. Require `admin-web` audience for Admin Auth. Map validation/auth/not-found/conflict/unavailable to canonical Connect codes and generated `KokoroErrorDetail`. Never expose raw Prisma errors.

- [ ] **Step 3: Run focused and package verification**

```bash
pnpm --dir kokoro-platform --filter @kokoro/platform-kit test
pnpm --dir kokoro-platform --filter @kokoro/platform-kit typecheck
```

- [ ] **Step 4: Commit**

Commit the interceptor slice independently.

### Task 6: Implement owner-local Admin Auth application service and receipts

**Files:**

- Create/replace: `kokoro-platform/kokoro-platform-admin/src/admin-auth-service.ts`
- Modify: `kokoro-platform/kokoro-platform-admin/src/admin-auth-store.ts`
- Create: `kokoro-platform/kokoro-platform-admin/src/admin-auth-receipt.ts`
- Modify: `kokoro-platform/kokoro-platform-admin/prisma/schema.prisma`
- Create: `kokoro-platform/kokoro-platform-admin/prisma/migrations/<timestamp>_admin_auth_receipts/migration.sql`
- Create: `kokoro-platform/kokoro-platform-admin/test/unit/admin-auth-service.test.ts`
- Create: `kokoro-platform/kokoro-platform-admin/test/integration/admin-auth-connect.test.ts`

- [ ] **Step 1: Write RED domain/service tests**

Cover normalized email, active/disabled operator, atomic token consume, duplicate same command/same digest, same command/different digest, duplicate auth event, receipt lookup, commit-before-response-loss reconcile, DB error sanitization and no token in receipt/log.

- [ ] **Step 2: Add the forward-only migration**

Use an additive owner table keyed by command ID with operation, request digest, state, safe result metadata, created/updated timestamps and unique idempotency identity. Do not store raw verification token in receipt JSON.

- [ ] **Step 3: Implement transactionally**

Within one Prisma transaction, lock/create the command receipt, apply the owner mutation once and commit the final receipt. A duplicate with the same digest returns the same result; a digest mismatch fails before effect.

- [ ] **Step 4: Run migration/unit/integration tests**

Use the isolated Admin test database and `prisma migrate deploy`; do not use `db push` as evidence.

- [ ] **Step 5: Commit migration and behavior together**

Include schema, migration, service, store and tests in one reviewable Platform commit.

### Task 7: Register the generated Connect service and remove hand-written transport

**Files:**

- Modify: `kokoro-platform/kokoro-platform-admin/src/server.ts`
- Modify: `kokoro-platform/kokoro-platform-admin/src/main.ts`
- Delete: `kokoro-platform/kokoro-platform-admin/src/admin-auth-rpc.ts`
- Delete/replace: `kokoro-platform/kokoro-platform-admin/test/unit/admin-auth-rpc.test.ts`
- Modify/Create nearest `INDEX.md` and README.

- [ ] **Step 1: Add a RED real HTTP/1.1 Connect test**

Start Fastify on an ephemeral port and use the generated Connect Node client. Assert success plus missing/wrong workload negative cases, canonical codes, deadline and receipt lookup.

- [ ] **Step 2: Register `fastifyConnectPlugin`**

Compose generated routes, validation, workload and error/metrics interceptors. Keep existing health/admin public routes on the same Fastify instance.

- [ ] **Step 3: Delete the hand-written route/version layer**

Remove `/internal/admin-auth/v1/*`, `x-kokoro-contract-version`, duplicated Zod schemas and transport-specific tests only after generated tests are green.

- [ ] **Step 4: Verify full Platform**

```bash
pnpm --dir kokoro-platform test
pnpm --dir kokoro-platform typecheck
pnpm --dir kokoro-platform lint
```

- [ ] **Step 5: Commit and push `kokoro-platform` owner branch**

Do not update the root gitlink until Web consumer and root compatibility pass.

---

## Chunk 3: Admin Web Connect Consumer and DB Removal

### Task 8: Add Web generated client dependencies

**Files:**

- Modify: `kokoro-web/apps/admin/package.json`
- Modify: `kokoro-web/pnpm-lock.yaml`
- Generated: `kokoro-web/apps/admin/lib/generated/contracts/**`
- Create: `kokoro-web/apps/admin/lib/generated/INDEX.md`

- [ ] **Step 1: Write RED import/bundle-boundary tests**

Assert the generated Admin Auth descriptor is importable only from server modules and cannot be reached from a `use client` dependency graph.

- [ ] **Step 2: Add exact dependencies**

Use exact `@connectrpc/connect@2.1.2`, `@connectrpc/connect-node@2.1.2`, and `@bufbuild/protobuf@2.13.0`. Do not add server framework or generator packages to Web runtime.

- [ ] **Step 3: Generate, test and commit dependency/mirror slice**

Run root generation, Admin test/typecheck and verify only Web lock changes.

### Task 9: Replace the hand-written Admin Auth client

**Files:**

- Replace: `kokoro-web/apps/admin/lib/auth/client.ts`
- Replace: `kokoro-web/apps/admin/lib/auth/client.test.ts`
- Modify: `kokoro-web/apps/admin/lib/auth/adapter.ts`
- Modify: `kokoro-web/apps/admin/lib/auth/adapter.test.ts`

- [ ] **Step 1: Write RED client-port tests**

Use an injected Connect transport. Cover operator not-found, disabled operator, create/consume command identity and digest, receipt reconcile after deadline, typed errors and no raw secret/email/token in error text.

- [ ] **Step 2: Implement the server-only client adapter**

Create the generated client with `createClient(AdminAuthService, createConnectTransport(...))`. Inject temporary workload metadata through one interceptor. Map generated messages to the narrow Auth.js domain port; do not expose Connect types to Auth.js adapter tests.

- [ ] **Step 3: Run GREEN**

```bash
pnpm --dir kokoro-web --filter @kokoro/admin-web test -- lib/auth/client.test.ts lib/auth/adapter.test.ts
pnpm --dir kokoro-web --filter @kokoro/admin-web typecheck
```

- [ ] **Step 4: Commit**

Commit the generated transport replacement without yet deleting Prisma.

### Task 10: Complete Auth.js wiring and delete Platform DB access

**Files:**

- Modify: `kokoro-web/apps/admin/auth.ts`
- Modify: `kokoro-web/apps/admin/lib/auth/events.ts`
- Modify: `kokoro-web/apps/admin/lib/env.ts`
- Modify: `kokoro-web/apps/admin/lib/env.test.ts`
- Delete: `kokoro-web/apps/admin/lib/prisma.ts`
- Delete: `kokoro-web/apps/admin/prisma/schema.prisma`
- Modify: `kokoro-web/apps/admin/package.json`
- Modify: `kokoro-web/pnpm-lock.yaml`
- Modify: `kokoro-web/apps/admin/README.md`

- [ ] **Step 1: Keep the existing RED env test**

The current test already proves Web must not require `DATABASE_URL_ADMIN`. Add static tests that `auth.ts` and `events.ts` contain no Prisma import and package scripts/dependencies contain no Prisma.

- [ ] **Step 2: Construct and inject one client**

Build it from `KOKORO_GATEWAY_URL`, temporary `KOKORO_ADMIN_PROXY_SECRET`, explicit audience and bounded timeout. Use it for adapter lookup, sign-in authorization and auth-event recording.

- [ ] **Step 3: Delete Prisma ownership artifacts**

Remove schema, client, generated scripts and dependencies. Update the lock mechanically with pnpm; do not hand-edit lock entries.

- [ ] **Step 4: Run full Admin verification**

```bash
pnpm --dir kokoro-web --filter @kokoro/admin-web test
pnpm --dir kokoro-web --filter @kokoro/admin-web typecheck
pnpm --dir kokoro-web --filter @kokoro/admin-web lint
pnpm --dir kokoro-web --filter @kokoro/admin-web build
```

Expected: all PASS; no `DATABASE_URL_ADMIN`, Prisma import, schema or dependency remains.

- [ ] **Step 5: Commit and push `kokoro-web` owner branch**

Do not update the root gitlink before live compatibility passes.

---

## Chunk 4: Session Platform Boundary (No GA Change)

### Task 11: Introduce `PlatformAdmissionPort`

**Files:**

- Create: `kokoro-session/src/platform/admission-port.ts`
- Create: `kokoro-session/src/platform/INDEX.md`
- Create: `kokoro-session/tests/platform-admission-port.test.ts`

- [ ] **Step 1: Write RED contract tests**

Define strict application types for `prepareRun`, `finalizeRun` and `getReceipt`; forbid raw HTTP response, fetch, Zod schema, Prisma/Mongo entity and GA-specific graph/checkpoint types from the public port.

- [ ] **Step 2: Implement the interface only**

The port represents the target boundary but does not claim remote atomicity. `prepareRun` returns accepted/denied/pending/outcome_unknown plus an opaque manifest/receipt reference. It accepts opaque `namespace` and upstream authorization references; it does not pass `ownerId/userId/workspaceId` into GA.

- [ ] **Step 3: Run focused tests/typecheck and commit**

```bash
npm --prefix kokoro-session test -- platform-admission-port.test.ts
npm --prefix kokoro-session run typecheck
```

### Task 12: Put existing behavior behind an explicit legacy adapter

**Files:**

- Create: `kokoro-session/src/platform/legacy-admission-adapter.ts`
- Modify: `kokoro-session/src/main.ts`
- Modify focused orchestration callers found by `rg 'billing|resolveModel|hub' kokoro-session/src`.
- Modify: `kokoro-session/tests/platform-admission-port.test.ts`

- [ ] **Step 1: Add RED characterization tests**

Capture current behavior and call order without changing billing/model/capability results. Assert callers depend on `PlatformAdmissionPort`, not concrete fetch clients.

- [ ] **Step 2: Implement the transition adapter**

Compose existing clients behind one file with an explicit `@deprecated remove in Platform Admission wave` marker. Do not add another network protocol, retry or error taxonomy. The adapter is a seam for later generated Connect replacement.

- [ ] **Step 3: Prove no behavior or GA change**

Run Session full tests/typecheck/lint and `git -C kokoro-agent diff --exit-code`; expected Agent diff is empty.

- [ ] **Step 4: Commit and push `kokoro-session` owner branch**

This commit is independently releasable and must preserve current HTTP/SSE behavior.

---

## Chunk 5: Federated Compatibility, Documentation and Promotion

### Task 13: Add the live Admin Auth compatibility scenario

**Files:**

- Create: `scripts/compatibility/admin-auth-connect.mjs`
- Create: `scripts/compatibility/admin-auth-connect.test.mjs`
- Modify: `config/repository/federated-repositories.json`
- Modify: `config/repository/compatibility-matrix.json`
- Modify: `scripts/compatibility/INDEX.md`

- [ ] **Step 1: Write RED runner tests**

Require exact Platform/Web participants, generated contract digest, isolated environment, real Platform Admin server, generated Web client, timeout/process-group cleanup and one closed FD3 machine result. Negative cases: missing credential, wrong audience, invalid request, contract skew and duplicate consume.

- [ ] **Step 2: Register the protocol**

Add `platform-admin-auth` v1: Platform provider, Web consumer, required live scenario. Do not list Session or Agent as participants.

- [ ] **Step 3: Implement and run live scenario**

Use the root selective Infra lease; initialize only Platform Admin owner DB through official migration commands. Do not read `.env` values into output.

- [ ] **Step 4: Verify scenario and repository governance**

```bash
node --test scripts/compatibility/admin-auth-connect.test.mjs
node --test scripts/repository/*.test.mjs scripts/compatibility/*.test.mjs
node scripts/repository/run-pinned-compatibility.mjs --matrix config/repository/compatibility-matrix.json --tree worktree --evidence tmp/admin-auth-compatibility.json
```

Expected: all required scenarios PASS with sanitized evidence.

### Task 14: Update architecture maps and remove stale claims

**Files:**

- Modify: `docs/CODEBASE_MAP.md`
- Modify: `docs/CURRENT.md`
- Modify: `contract/README.md`
- Modify: child README/INDEX files touched above.
- Create: `docs/reports/2026-07-27-contract-foundation-admin-auth-pilot-verification.md`

- [ ] **Step 1: Update facts only after code passes**

Record Proto/OpenAPI/Event authorities, generated mirrors, actual Web upstreams, no Admin DB access, Session admission seam, commands and exact verification evidence. Do not describe later Admission/SSE waves as implemented.

- [ ] **Step 2: Run document/governance checks**

Run `rg` for stale `DATABASE_URL_ADMIN`, Prisma Admin imports, hand-written Admin Auth paths/version header and incorrect “Web only consumes Session” statements.

- [ ] **Step 3: Commit root docs/report**

Keep verification evidence factual and secret-free.

### Task 15: Final verification and gitlink promotion

**Files:**

- Modify: four child gitlinks only for children with verified commits.
- Modify: `config/repository/federated-repositories.json` pins/recoverable refs.
- Modify BOM/compatibility evidence files required by the root repository policy.

- [ ] **Step 1: Review every child diff and commit**

Confirm no generated file was hand-edited, no sibling import, no Agent change, no secret, no Web Prisma and no unrelated user change.

- [ ] **Step 2: Run child verification from the main worktree**

Do not rely on worker exit status. Run Platform full tests/typecheck/lint, Web Admin full tests/typecheck/lint/build and Session full tests/typecheck/lint.

- [ ] **Step 3: Run root contract/governance tests**

```bash
pnpm --dir contract install --frozen-lockfile
pnpm --dir contract run buf:lint
node scripts/repository/check-generated-contracts.mjs
uv run python contract/check.py
uv run pytest contract/tests -q
node --test scripts/repository/*.test.mjs scripts/compatibility/*.test.mjs
```

- [ ] **Step 4: Run clean recursive clone verification**

Clone the exact root candidate recursively into a temporary directory, install each exact lock, regenerate contracts and rerun the live Admin Auth plus existing required compatibility scenarios.

- [ ] **Step 5: Promote exact child commits**

Update gitlinks, artifact/contract digests and recoverable refs only after all prior gates pass. Commit root promotion separately from child implementation.

- [ ] **Step 6: Remove test containers**

Stop/remove containers created for the verification scope while retaining shared images/cache unless space policy requires otherwise. Report exactly what was removed.

---

## Completion Gate

This pilot is complete only when all of the following are evidenced:

- Root Proto/Buf source generates deterministic Platform/Web mirrors.
- Buf lint and breaking policy run in CI.
- Admin Web uses generated Connect client and has zero Platform DB/Prisma ownership.
- Platform Admin is the only writer of operator/token/auth-event/receipt tables.
- Duplicate/digest mismatch/timeout-after-commit/receipt recovery are tested.
- Static shared secret is isolated to one temporary interceptor, not read by handlers.
- Session has one `PlatformAdmissionPort`, behavior unchanged, and GA diff is empty.
- Root live provider/consumer scenario passes from exact child commits.
- Clean recursive clone reproduces generation, build and compatibility.
- Documentation reflects only implemented facts.
