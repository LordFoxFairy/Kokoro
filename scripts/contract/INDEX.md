---
architectureIndex: 1
rootId: root.scripts.contract
owners:
  - "@LordFoxFairy"
---

# Contract boundary governance

## Responsibilities

Prove that every cross-repository boundary is registered, that each registered operation is backed by a real
contract source, and that each operation is frozen to exactly one transport.

## Non-responsibilities

This gate reads declared contracts only. It does not prove wire behaviour, authorization, deadline enforcement,
receipt durability, or that a provider actually implements a registered operation. It does prove the narrower
structural facts that a protobuf `command-receipt` ref is reachable through the RPC response descriptor and that a
`reconcile_receipt` command/state receipt names a non-effect recovery operation in the same boundary.
For protobuf, that recovery request must carry either command-id/digest identity or a dedicated transaction/proof pair,
and its response must reach the same fully-qualified receipt type. For OpenAPI state reads, the recovery
operation must be a real GET with a declared 200 response. A same-named type from another protobuf package is rejected.

## Public boundary

`check-boundary-registry.mjs` is the supported entrypoint; `check-boundary-registry.test.mjs` defines its
fail-closed behaviour. Policy data is [`contract/registry/boundaries.yaml`](../../contract/registry/boundaries.yaml),
described by [`contract/registry/boundaries.schema.json`](../../contract/registry/boundaries.schema.json).
The registry is JSON-compatible YAML, following `config/architecture/index-roots.yaml`: the filename the spec
mandates, without adding a YAML parser dependency.

`check-web-release-composition.mjs` is the offline publication-contract gate for ADR-016. It compiles all fifteen
JSON Schema 2020-12 documents with strict AJV, then verifies the closed owner registry, I-JSON/NFC input profile,
RFC 8785 JCS SHA-256 vectors, DSSE PAE/Ed25519 vectors, exact Catalog-to-Inventory partition, owner digest chain,
exact composition-registry projection, measured tool role/ref/digest bindings, compiled unit/package/route/BFF/model
closure and SLSA/in-toto provenance binding through global, role-specific dependency URIs. Tool roles and package refs
are encoded into their dependency URI identities; duplicate package name/version identities and any URI collision fail closed. Canonical vectors must
cover every positive case exactly once; DSSE vectors must cover exactly the registry rows whose signature profile requires DSSE.
The corpus also freezes persisted, digest-bound activation authority snapshots at attempt start and immediately before
pointer CAS, plus eligibility evidence that references both distinct reads. Every snapshot binds six owner-signed current
head receipts and the exact active-pointer CAS precondition. Candidate/certification revocation, key revoke/suspend,
ProducerRegistry or TrustPolicy epoch drift, or expiry between snapshots fails closed before CAS. DSSE test vectors carry
only payload/signature facts; trusted public keys and current epochs come exclusively from Root's producer registry.
It explicitly keeps Product Catalog and
Site business ownership out of Root and keeps unit selection out of Platform. Existing v1 registry rows and schemas
are immutable under `--breaking-against`; the predecessor may contain its own valid subset, while the candidate must
contain the complete current set. The one unpublished R0a owner-closure hard cut is executable only through the exact
predecessor/candidate digests in `contract/registry/prelaunch-schema-hard-cuts.yaml`; the registry rows themselves and any
unlisted or follow-up drift still fail closed.

`check-prelaunch-protobuf-breaking.mjs` wraps the pinned Buf breaking gate for the matching unpublished protobuf cut. It
validates the exact contract-only exception registry, candidate source bytes and Git baseline bytes before excluding the three
recorded Site files. Once the candidate is the baseline it passes no exclusions to Buf, so the waiver cannot become permanent.
It does not prove or claim Product Catalog, Site Publication, Provisioning, or Lifecycle runtime providers.

OpenAPI descriptors are different: they are full YAML 1.2 documents and may legitimately use anchors, flow
mappings, merge keys, and quoted scalars. `openapi-reader.mjs` invokes the root-lock-pinned PyYAML reader in
`read-openapi.py`; its SafeLoader extension rejects duplicate keys before returning a JSON document. Both the
registry parity gate and the Wave 1 surface gate consume this one reader, so a second partial indentation parser
cannot silently omit an operation or an operation-level `security: []` override.
The pinned Redocly CLI independently runs its OpenAPI 3.1 `spec` ruleset in CI; custom ownership/security checks
complement that validator and never replace structural validation.
Protobuf inventory, request/response fields, nested receipt reachability, namespace-axis isolation, and the allowed
`RetryClass` set come from descriptor sets built by the pinned Buf binary. Comments, formatting, or same-named types
in another package therefore cannot satisfy a registry claim.

Media caller fingerprints are produced only by the Root-owned TypeScript/Python deterministic-protobuf generators.
One descriptor-backed manifest drives both pure-language runtimes; their shared corpus includes hostile object keys,
Unicode scalar and UTF-8 byte-boundary vectors. Projection record and head integrity is independently checked by
`contract/validate-projection-integrity.mjs`, which applies strict resource budgets, canonical descriptor decoding,
the full pinned Protovalidate rule set, SHA-256 recomputation, and Ed25519 verification. The public corpus is rebuilt
reproducibly by `contract/generate-projection-integrity-corpus.mjs` from semantic fixtures and a test-only seed.

`check-wave1-surface.mjs` freezes the complete 53-operation Site BFF set, including the 16 image-first
Media/Artifact operations. Ordinary POST effects require contract version, idempotency and CSRF headers. The two
ephemeral credential issuers—Session access and exact Artifact-version delivery authorization—are explicit
exceptions: they require contract version plus CSRF and reject both command identity and idempotency headers, because
response loss must create a new independently revocable grant instead of replaying bearer material.
Its privileged protobuf service/method/field checks use the same Buf descriptors as the registry gate. Forbidden
public identity axes and legacy/payment routes are traversed from parsed OpenAPI keys and values, so YAML quoting and
flow mappings cannot hide them while comments remain non-contractual.

`check-boundary-coverage.mjs` is the companion source-to-registry gate. It scans the two internal runtime
consumers (Session and Agent), reduces Session's Platform service dependencies and Agent's Hub/LiteLLM
dependencies to unique service edges, and requires an `active` registry entry with both the exact provider
boundary and the actual consumer.
Repository-pair matching is intentionally insufficient: `service.platform` cannot vouch for `platform.hub`,
and neither can vouch for `platform.litellm`. Web's public BFF plane is outside this narrow scanner and remains
covered by the Admin/OpenAPI and Session browser gates rather than being silently claimed here.

`check-agui-presentation.mjs` is the public, read-only strict AG-UI presentation gate;
`check-agui-presentation.test.mjs` defines its fail-closed public behaviour. It loads only the fixed reviewed Root
role profile, Agent candidate profile, mapping, schemas, and corpus—callers cannot inject validators or alternate branded paths—and imports the
official `EventType` and `EventSchemas` from exact `@ag-ui/core@0.0.57`. The contract package and lock must retain
that exact version and integrity. Every positive event must satisfy both the official schema and Kokoro's smaller
closed vocabulary; forbidden raw, provider, native-tool, reasoning/thinking, state/delta, and unknown-custom
families never become presentation data merely because upstream accepts them. The Agent candidate gate is narrower again:
it admits safe RUN/TEXT/ACTIVITY candidates only, rejects `CUSTOM` and Artifact/Cost owner activities, and verifies each admitted
sample through the official `EventSchemas`. The envelope gate recomputes RFC 8785/JCS event bytes, rejects invalid Unicode scalar
strings and unsafe/non-finite numbers, verifies the event digest and domain-separated candidate ref, and binds route refs and
canonical recorded time back to the event. All event/content keys remain closed by schema, so Unicode object-key ordering cannot
be injected through a dynamic map. Its independent Agent source fixtures are ordered as the owner log within each internal run:
the first ordinal is zero, later ordinals strictly increase, source refs are unique, and the fixture vector is deliberately not
the Session durable-sequence vector. Session may persist the Agent source ref as provenance but owns and assigns `durableSeq`.
Agent `internalThreadRef` is a closed `agent.thread:<opaque-id>` owner ref: ordinal-zero `RUN_STARTED` establishes
the thread authority for its internal run and every later candidate must match it. This replaces origin guessing from
Session-shaped string content with a branded type plus an explicit authority relation. Agent `RUN_STARTED` cannot carry
`parentRunId`; projection derives that browser field only from Session's run-binding authority.
It records no Agent runtime activation.

`check_agent_agui_python_parity.py` is the opposite-direction executable promotion gate. It verifies Root, Agent
pyproject/lock, installed `ag-ui-protocol`, and TypeScript/Python profile pins resolve to the same upstream commit; then it
reconstructs all registry-declared candidate event arms and activity discriminators from official Python event models and
Agent's public builder and requires exact JSON-object equality. Coverage is derived from the registry rather than a static
sample count, so registry additions, removed arms, duplicate substitutions, activity omissions and semantic role drift fail
closed. The gate is activated in CI only together with the reviewed Agent gitlink/manifest/BOM promotion. Its test module
freezes pin, digest, duplicate, registry drift, activity and source-coverage failures. This is build-time cross-repository evidence only:
Agent never reads Root files at runtime and the dormant adapter is still not wired into execution or browser transport.

`generate-agui-presentation-corpus.mjs` deterministically derives the public conformance cursors and persisted
projection rows. Its default mode rewrites the checked-in corpus; `--check` is non-mutating and compares exact bytes.
The public AES-GCM key is conformance-fixture material only, never a runtime key. The gate decrypts every snapshot
and frame cursor into closed Session/epoch/sequence/profile claims, rejects both byte and semantic identity reuse
across positive cases, binds all run/message/source/row identities to their Session, verifies real parent lineage,
and requires the persisted complete projection payload plus its JCS SHA-256 to equal the emitted frame exactly.
Snapshot cases additionally prove the Session durable-head `lastRecordedAt` rule, canonical UTC-millisecond representation,
binding-time lower bound, and canonical next-event non-regression. A checked-in six-vector attack corpus also rejects a zero
head carrying bindings, evidence cardinality beyond the head, noncanonical binding time, multiple presentation threads,
cyclic parent lineage, and M0 interrupted/canceled terminal state. It does not pretend the browser snapshot contains Session's
complete historical source-ID ledger.
It proves an offline `contract-only` Session projection profile; it does not prove a Session/Web runtime adapter,
deployment, authorization, or compatibility scenario.

`check_admin_openapi.py` is the supported entrypoint for the Admin browser plane, and
`test_check_admin_openapi.py` defines its fail-closed behaviour. The companion
`inspect_admin_browser_sources.mjs` uses the Web-pinned TypeScript compiler AST to inventory Fastify
registrations in `kokoro-platform/kokoro-platform-admin/src/server.ts` and top-level exports in
`apps/admin/app/api/**/route.*`. The gate requires exact set equality with
[`contract/openapi/admin-web-v1.yaml`](../../contract/openapi/admin-web-v1.yaml), so a route added,
removed, aliased behind an unverified receiver or method reference, or re-verbed on either side fails.
TRACE, custom Fastify HTTP shorthands, and other methods unavailable to Fetch are recognized and
rejected instead of disappearing from the inventory. For transparent Web
authority it executes the actual `next.config.ts` `rewrites()` under a credential-free fixed production
environment and validates every fallback source and destination; a source-only text list cannot provide evidence.
Transparent paths inherit the exact provider method set, while local handlers must declare the exact
callable methods at the top level. Their union must equal the OpenAPI operation set, while duplicate
ownership, orphan/missing operations, unreadable dynamic routes, and local method drift all fail.
Auth.js's local `/api/auth/*` owner is explicitly outside this Platform contract. `--openapi`,
`--server`, `--proxy`, and `--local-routes` take alternate paths for fixtures. It is Python because that
document is hand-written YAML carrying comments and the root workspace already provides PyYAML; the
sibling registry gate stays on Node because its data is JSON-compatible.

`check_admin_browser_schemas.py` is the supported entrypoint for the other end of that plane, with
`test_check_admin_browser_schemas.py` defining its fail-closed behaviour. It proves the browser's
hand-written readers in `kokoro-web/apps/admin/lib/schemas.ts` do not contradict the published
contract: every field the browser reads must be declared by the contract schema it is mapped to.
`--openapi` and `--schemas` take alternate paths for fixtures.

`test_admin_browser_public_shapes.py` is the narrow exact-shape companion for filtered responses. It
requires the Root `User360` schema, the Admin BFF's positive `user360EnvelopeSchema.data`, and the
browser's `user360Schema` reader to publish the same closed field set in both directions. It also freezes
the bounded non-payment module OpenAPI operation so an upstream Platform payload may stay wider without
re-publishing acquisition data to the browser.

It is a gate rather than a generator on purpose. Generating the browser validators from the contract
would *lose* checking for part of this surface: the gateway validates downstream rows only to
`z.array(z.record(z.unknown()))`, so `ResourceRow` is declared with no properties and
`additionalProperties: true` (open decision D4). The hand-written Site, credit-account, and identity
readers name the fields their screens consume, so they currently encode more field knowledge than the
contract does. The readers also stay deliberately lenient — a dirty row degrades one row instead of
blanking the page. These three readers map onto `ResourceRow` and therefore cannot be verified at all;
that count is printed on every run rather than presented as coverage. When D4 lands, the count drops
and generation becomes the better answer for those three.

## Callers and dependencies

Root CI and contract owners call the checks. They read `contract/proto/`, `contract/spec/`,
`contract/openapi/`, `config/repository/compatibility-matrix.json`, `config/architecture/index-roots.yaml`,
`kokoro-platform/kokoro-platform-admin/src/server.ts`, `kokoro-web/apps/admin/next.config.ts`, the Admin
local Route Handler tree, and `kokoro-web/apps/admin/lib/{admin-gateway,schemas}.ts`, and write nothing.

## Data ownership and events

The registry owns boundary inventory: owner, repository-level consumers, boundary audience, protocol, deadline,
retry class, receipt, failure owner, and how each operation binds its Site. Privileged operations may additionally
freeze a closed method-level `trustedCallers` list of role/audience pairs. The provider must derive that pair from
authenticated SPIFFE server context; the checker rejects protobuf request fields that try to self-assert caller role,
caller audience, or SPIFFE identity. Wire shapes stay owned by `contract/proto/` and
`contract/spec/`; this directory never becomes a second authority for them.

## Runtime and security

Read-only and deterministic, with no runtime network: protobuf gates use Root-pinned Buf and
`@bufbuild/protobuf`; projection validation additionally uses the exact pinned `@bufbuild/protovalidate` runtime,
while strict AG-UI validation uses the exact pinned `@ag-ui/core` runtime only as the official schema authority.

The two Platform projection-recovery boundaries keep `GetProjectionHead` and `PullProjectionEvents` pure reads and register
`RefreshProjectionRecoveryAccess` as a `same_identity` command-receipt effect. Media and Credit use separate typed effects
and digest helpers, while the common projection-integrity contract owns the monotonic access/refresh credential envelope.
OpenAPI parsing and the Python gates use PyYAML, which the root workspace already pins. Source paths must stay
repository-relative and are rejected if they escape the repository.

## Idempotency, failure, and recovery

Repeated runs on unchanged inputs produce the same single-line result. Any violation exits nonzero with sorted
`snake_case` codes naming the offending boundary, operation and path.

## Extension rules and forbidden dependencies

Register a new boundary in the same change that introduces it, and keep it in step with the compatibility
matrix according to lifecycle: `active` must appear with real runtime evidence, while `contract-only` must remain
absent until provider and official consumer exist. Declare `sourceStatus: "machine-readable"` only with a real contract source behind it; a boundary
with no source in this repository must say `declared-only` and be counted, never claim coverage it does not
have. Allowed retry classes are derived structurally from the `kokoro.common.v1.RetryClass` descriptor; never hardcode that list here.
New privileged effects use `kokoro.common.v2.CommandIdentityV2` and `CommandReceiptV2`: generated digest helpers
bind exact typed effect bytes to canonical scope, Site, actor and resource sets. Admin Command v2 additionally binds
operator generation, assurance/factor classes, authentication/step-up instants, and the operator attestation digest
to server-verified axes before digesting. V1 remains byte-frozen for legacy consumers. A registry row must name the matching response receipt version; a V1 registry ref cannot silently
vouch for a V2 response. `reconcile_receipt` is not documentation shorthand—command/state receipts must name the
actual read operation callers use after an outcome-unknown response.

## Current gotchas

Two blind spots are recorded rather than hidden, and both appear in every successful run.

`model-gateway` is `declared-only`: it is the LiteLLM OpenAI-compatible face and this repository holds no
contract source for it, so its operations get no orphan check at all. It is the one boundary that can drift
without the gate noticing, which is exactly why the count is printed.

Site binding is explicit and every count is printed. `request-field` means the provider validates an
owner-authoritative Site field on the operation itself; the gate proves that claim against the operation's
own request shape. `workload-binding` derives Site from an authenticated deployment identity rather than
browser input. `capability-binding` is reserved for a sealed, owner-issued bearer capability whose Site and
revocation axes are revalidated against current owner state on every request. Browser multipart upload uses
that form; CORS preflight is separately platform-scoped and conveys no Site authority.

`context-header` is the weaker of the two claims and is not proven at all: the gate cannot see whether a
provider reads the header it is declared to read. `list_model_labels` was declared `context-header` while its
handler ignored the header entirely and applied no Site filter — the caller sent it, so the declaration
looked satisfied from the wire. Treat the count as unverified debt, not as coverage.

`platform-admission` is the first `contract-only` boundary: its shape is published in
`contract/proto/kokoro/platform/admission/v1/admission.proto`, but no provider implements it, so it is
deliberately absent from the compatibility matrix. The matrix drives the runtime gate, and listing an
unimplemented protocol there would assert a capability that does not exist. Registering it as `active`
before a provider ships fails.

The `request-field` proof recursively walks the exact RPC request descriptor for proto sources. For spec YAML it depends on how the
source declares operations: when their ids derive from object names the proof is per operation, resolved
against that operation's own request object. Only a block-mapping section such as `endpoints`, which
declares no fields of its own, still falls back to a file-wide match — weaker evidence, so those operations
are tracked separately rather than presented as per-operation proof. The file-wide form previously applied
everywhere, which let one object's `siteId` vouch for siblings that had none. Every `deadlineMs` is
`null` because no boundary declares a deadline in code yet; that is a recorded fact, not an implied default.

The Admin gate scopes itself to the browser plane and names its exclusions rather than skipping them
quietly: `/` serves HTML, `/healthz` and `/metrics` are probe endpoints registered by platform-kit
helpers, and `kokoro.platform.admin.v1.AdminAuthService` is the privileged Connect plane the transport
spec keeps separate. Declaring an excluded path in the document fails, and an unrecognised
`register*Route` helper fails too, because such a helper registers routes this gate cannot see.

## Verification

`check-model-control-admin-read.test.mjs` locks the privileged Model Control read plane to typed,
bounded projections. It requires all nine inventory, option, Site-policy, and Site-release catalog
operations and rejects any provider projection that exposes the persisted secret reference. The
generated-contract repository gate treats `platform-model-control@v1` as a live two-party boundary:
Platform owns the provider mirror and Web owns the Admin BFF consumer mirror.

The same gate owns the machine-readable browser recovery protocol in
`contract/spec/model-control-browser-recovery.yaml`. Model effects use stateless prepare→execute:
prepare validates but cannot execute, the browser persists one bounded opaque reference before execute
and never persists the large command body, and execute must reauthorize and recompute the canonical
operation/Site/digest while retaining the prepared UUIDv4. Response loss is reconciled against the
Platform typed receipt. Only authoritative `committed` evidence unlocks another effect; NotFound,
timeout, invalid recovery, and operator confirmation retain the pending lock.

Model Admin unary calls have one explicit end-to-end transport budget: requests are limited to 16 MiB
and responses to 8 MiB in both the Platform Admin Connect server and Web Admin Connect client. The Web
BFF admits semantically valid inventories above the former 64 KiB ceiling and reports an over-budget
browser body as HTTP 413 `request.payload_too_large`; field-level Buf Validate failures remain HTTP 400.
The budget is intentionally not the Cartesian product of every repeated-field maximum. Every repeated
identifier/reference item is independently bounded in `model_control.proto`, while the total unary budget
is the operational resource boundary.

`platform-model-control@v1` also generates `model-control-errors.ts`. Platform must use this artifact
when producing inventory-not-found, command-receipt-conflict, Admin-page-token, authentication, and
authorization errors, and Web must consume the same classifications when asserting HTTP status and safe
domain-code projection. This
keeps Connect error details executable across the provider/consumer split instead of duplicating literals.

Run `node --test scripts/contract/*.test.mjs` followed by `node scripts/contract/check-boundary-registry.mjs`,
`node scripts/contract/check-boundary-coverage.mjs`, `node scripts/contract/check-web-release-composition.mjs`,
and `node scripts/contract/check-wave1-surface.mjs`,
then `node contract/generate-projection-integrity-corpus.mjs --check` and
`node contract/validate-projection-integrity.mjs --validate-corpus`,
`pnpm --dir contract run openapi:lint`,
then `uv run --locked python -m pytest scripts/contract/test_check_admin_openapi.py
scripts/contract/test_check_admin_browser_schemas.py
scripts/contract/test_admin_browser_public_shapes.py -q`,
`uv run --locked python scripts/contract/check_admin_openapi.py` and
`uv run --locked python scripts/contract/check_admin_browser_schemas.py`.

The strict AG-UI sub-gates are `pnpm --dir contract agui:check`,
`pnpm --dir contract agui:typecheck`, and `pnpm --dir contract agui:test`.

The Node checks need no install; the Python ones need `uv sync --locked` first. Both were replayed
from a bare recursive clone at the pinned state. Read exit codes directly rather than through a pipe,
which reports the last command's status instead of the gate's.
