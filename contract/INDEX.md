---
architectureIndex: 1
rootId: root.contract
owners:
  - "@LordFoxFairy"
---

# Cross-repository contract source

## Responsibilities

Own versioned protobuf, OpenAPI, and legacy compatibility schemas plus deterministic generation inputs.

## Non-responsibilities

This directory does not implement providers, consumers, retries, authentication policy, or business orchestration.

## Public boundary

`proto/`, `openapi/`, `spec/`, `buf.yaml`, `buf.gen.yaml`, `generate.mjs`, `generate.py`,
`generate-public-openapi.mjs`, both Media canonical generators, the canonical and projection-integrity
golden corpora, the Web Release Composition JSON Schema/registry/corpus family, the semantic projection corpus
generator, the descriptor/Protovalidate integrity validator, and the
generation/check commands documented in [`README.md`](README.md) form the public boundary.

## Callers and dependencies

Platform, Session, Web, and Agent consume committed generated mirrors or declared wire schemas at their own pins.

## Data ownership and events

Contracts describe wire data; they do not own persisted business records or emitted runtime events.

## Runtime and security

Generation is deterministic and temporary check mode must not rewrite child working trees. Sensitive defaults are forbidden.
Projection corpus generation uses a deterministic test-only Ed25519 seed that is never emitted; validation bounds corpus,
descriptor, record, identifier, repeated-field, nesting, signature, key, subprocess time, and subprocess output resources.
The public Site client generator deliberately removes OpenAPI server locations and emits only strict request/response schemas,
relative operation paths, exact success statuses, and contract metadata. One default generation updates the byte-identical Platform
provider and Site Web consumer mirrors; an explicit `--output` is restricted to the system temporary directory. Site runtime binding
resolves the actual Platform target.

## Idempotency, failure, and recovery

Repeated generation from the same source and tool versions must be byte-identical. Drift is a hard failure before pin promotion.
Model Control effects expose `GetCommandReceipt`; callers reconcile an ambiguous timeout/Unavailable outcome by the original
32-hex command ID, expected operation, and exact Site scope before considering a same-identity replay. Receipt results are typed
safe projections of the five Model Control effects, never generic Admin resource payloads.

## Extension rules and forbidden dependencies

Add a schema only with a real producer and consumer. Never create runtime filesystem coupling from a child to this directory.

## Current gotchas

The fifteen Web Release Composition v1 contracts are offline publication contracts, not a runtime boundary and not a
new service. Root owns their schema, I-JSON/RFC 8785 canonical profile, compatibility freeze and corpus; Platform
Product Catalog owns Product/Surface/Journey business records, Platform Site owns inventory/material/intent, and Web
Release Composition owns toolchain/composition-registry/compiled-manifest/provenance publication. Payloads never contain their own digest
or signature. Callers carry the digest when referencing another immutable payload; DSSE signatures and the final OCI
artifact digest live outside the signed/canonical payload, preventing a digest cycle. Provenance dependencies use
global `git+https:`, `oci:`, `pkg:`, or `kokoro:` URIs: tool URIs include the measured role and repository ref,
while package URIs retain the package URL identity and include the unique composition package ref.

`PublishSiteReleaseEffect` is a latest-only Admin command: callers provide only `site_release_candidate_ref`,
`expected_candidate_version`, and `reason`; Platform generates the immutable SiteRelease and all authority-bound facts.
The `platform-site-provisioning@v1` boundary remains `contract-only`. The old Platform publish handler is now fail-closed,
but Candidate Authority remains dormant until Platform and Web regenerate their mirrors from this Root source and submit
provider/consumer compatibility evidence. Root contract publication does not claim that runtime migration is complete.

DSSE verification resolves SPKI only from `contract/registry/trusted-web-release-producers.yaml`, never from corpus vectors.
Every Ed25519 trust anchor declares an exact producer role plus allowed contract ids, payload types and owner-receipt aggregate
kinds; certification-instance and revocation authority are intentionally disjoint even when their audience is identical. The
signed tuple binds key id/version/fingerprint, producer registry and trust-policy current epochs, audience, environment,
validity and active status. Activation snapshots persist six independently signed owner live-read receipts—Candidate,
Certification, ProducerRegistry, TrustPolicy, signing-key status and active pointer—plus Site/environment, activation and CAS
command refs, nonce/fence, expected pointer generation and the exact CAS precondition. A first activation is represented
explicitly with a null current release and generation zero.

Eligibility time is bounded by the signed immediate-before-CAS active-pointer receipt: its server-issued time derives a fixed
five-second freshness lease, and both snapshots must be no more than 120 seconds old. Persisted evidence is audit material,
not a reusable authorization token. The runtime active-pointer CAS transaction must re-read the authoritative database rows
and revalidate them against database `now` inside that same transaction before swapping the pointer.

Protobuf sources are authoritative for privileged Connect boundaries; OpenAPI is authoritative for browser/Site public HTTP;
older YAML schemas remain authoritative only for the legacy boundaries that still consume them. Legacy TypeScript mirrors use
the explicit two-argument Zod record form so Zod 3 and Zod 4 consumers remain byte-identical during the toolchain transition.
Browser v3 Submit keeps renderable `parts` and Asset-owned `attachment_refs` separate. The generator's
`require_nonempty_any` object constraint admits either source while rejecting an empty command; each text part remains non-empty.

`AdminCommandService.v2` is a fresh-only maker/checker/worker contract. Browser clients may call only
`SubmitCommand`, `DecideApproval`, and `GetReceipt`; approval queues execution and never
grants a client execution method. Its generated digest helper binds every caller-declared operator generation,
assurance/factor, authentication/step-up instant, and attestation axis to the server-verified transport/session axes.
The removed Prepare/SubmitForApproval/ExecuteApproved authority is intentionally unreachable and has no adapter.

`AdminCommerceService.v1` is the fresh-only typed operator ingress for Commerce catalog and card administration. It exposes a
closed method set—no arbitrary route/action proxy—and binds every effect to Site scope plus the shared authenticated operator
command envelope. CreditProgram and EntitlementTemplate prerequisite revisions publish through their own typed immutable
operations before `PublishOffer` may reference them; both have Site-scoped list/get recovery surfaces. `PublishOffer` is one atomic
immutable graph publication. Card secrets exist only in the first committed
`IssueCodeBatch` response (maximum 1,000), while replay and all query types expose only delivery-unavailable state, counts and safe
export receipt metadata. Code-batch approval and lifecycle transitions remain Commerce-owned database invariants.

`AdminCreditService.v1` is the dedicated read-only operator plane for Credit authority facts. Every request binds an exact Site,
uses bounded opaque keyset pagination, and exposes decimal amounts as strings. Site/account summaries identify their authoritative
database observation. Paginated responses distinguish the immutable membership cutoff (`membership_watermark`) from the database
time at which each page was observed (`observed_at`). Source filters are the exact `(source_type, source_ref)` identity, never a bare
reference. Hold and RatedUsage allocation surfaces preserve bidirectional traceability through Grant without exposing rating
snapshots, raw usage evidence, provider payloads, secrets or legal-liability dimensions.

ADR-014 hard-cuts the unpublished `agent-execution-evidence` registry boundary to V2. An Interaction is published only
as one bounded, ordered `InteractionGroupRevisionEvidenceV2` envelope: every member carries the stable owner ref,
monotonic revision, exact predecessor ref/digest, application request, frame fence and closed safe presentation. A
half-group has no wire representation. Lifecycle evidence and the independent append-only output sequence remain
read-only; output sequence numbers never share or advance lifecycle `durable_seq`.

`session-agent-control@v2` is the matching durable control boundary. `RunResumeV2` binds one exact group revision and
ordered decision vector without exposing any graph route. Sensitive decision values are typed encrypted envelopes.
The stable resume receipt is projected as immutable predecessor-linked receipt events; an authenticated bounded
`GetRunResumeReceiptEvents` read repairs gaps without overwriting history. Both V2 boundaries are machine-readable,
generator-isolated and `contract-only`; neither appears in the active compatibility matrix until the real providers,
official consumers and runtime assertions ship together. V1 files remain historical inputs only and are not advertised
or double-written. `corpus/interaction-identity-v2.json` freezes all nine canonical ref planes using domain-separated
SHA-256 and decimal-string revisions.

ADR-015's image-first foundation publishes six isolated Protobuf bundles without claiming a runtime:
`platform-media-runtime@v1` (GA to Platform Media), `model-image-effect@v1` (Platform Media to Model Gateway),
and `session-media-projection@v1` (Session-owned reservation, pending binding, activation recovery, replacement,
and separate Media/Credit access), `session-media-projection-ingest@v1` (the authenticated Connect delivery entry),
plus separate Media-owner and Credit-owner projection recovery bundles.
The image-effect `ACCEPTED` state means only that Gateway durably committed the command, Attempt authorization and
dispatch outbox. Provider `SUBMITTED` is a later owner observation; queue acceptance, lease ownership and transport send
never imply it.
Root also generates the image-effect Create/Cancel/Attach/OutputAccess command digest helper from typed known fields.
Rotating access and source bearer bytes are excluded, while verified caller/site/security epochs and stable grant digests
remain bound. Final output facts are read by owner cursor; a separate recoverable command issues short-lived source access,
and Artifact consumes it only through the bounded server-streaming data plane.
Durable `MediaProjectionBindingCommitted` must activate a pending binding
before ordinary Media projection events; Media carries only the Credit-owned cost projection ref/version, while
Credit publishes amount/state through its own audience-bound event. All six generated Media/Image/Session contract
families (eight registry boundaries including the two durable event planes) remain `contract-only` and absent from runtime compatibility until real providers and official consumers
ship. Recovery requests use command ref plus opaque access only; owner HMACs, original inputs, Provider payloads,
and top-level Generation/Job identities are not part of these contracts.

`PrepareRunEffect.session_projection_authorization_handle` is a required Session-owner-issued capability bound to
the committed launch/Run/message and current owner epochs. Platform Admission may only forward it into
`IssueMediaProjectionReservation`; it is forbidden from public OpenAPI, safe admission snapshots and prepared
authorization responses. Projection control and ingest methods declare closed caller role/audience pairs in the Root
registry. Runtime authorization derives those pairs from authenticated SPIFFE server context, never from request fields.
Durable Media/Credit records remain the owner truth. BindingCommitted first delivery and retries both use the canonical
`RecoverMediaProjectionActivation` method and its dedicated activation receipt; only Media sequence >= 2 and Credit's
independent sequence >= 1 cost records use the ingest Connect service, which returns a typed durable receipt with exactly
`applied|replayed|pending_gap|rejected|suppressed` outcomes. CEL also closes the recovery decision: gaps recover the
exact missing predecessor, integrity rejection contacts support, owner-fence rejection reconciles the owner, and all
successful/replayed/suppressed receipts require no action. A temporary missing response retries the same immutable event
under registry policy rather than fabricating a receipt outcome.

Projection event identity is split from delivery capability: immutable Ed25519 owner-signed records carry source sequence,
predecessor ref/digest and content; short-TTL Session target handles and complete owner recovery credentials live only in
delivery envelopes. Owner recovery read access and refresh authority are separate bearer values. The common envelope binds
an issued-at anchor, monotonically increasing access generation, access/refresh expiries, and an explicit previous-generation
invalidation or bounded overlap. Replaying a delivery keeps the same record ref/digest/signature. Session repairs gaps and
builds shadow generations through pure read-only `GetProjectionHead` / bounded `PullProjectionEvents` Connect services for
Media and Credit; neither read rotates credentials or returns replay authorization, and neither owner can read the other's
projection facts. Rotation is a separate `RefreshProjectionRecoveryAccess` V2 command-envelope effect. Its expected
generation and owner-chain refs are part of the typed digest; a committed response persists the exact next credential and
receipt so a response-loss retry with the same identity returns the same result. `projection-integrity.yaml` is the
sole manifest for all five signed message descriptors, their domain separators, excluded digest fields, signature fields,
forbidden credential fragments, and validation budgets. The reproducible Ed25519 corpus proves canonical wire form,
digest/signature verification, and authenticated Protovalidate rejection on every signed surface. Signed heads never
contain rotating recovery handles.

The `platform-public@v1` Site BFF surface also publishes the image-first product ingress without a second public
protocol: nine Media operations cover immutable definitions, safe model options, non-binding quotes, submit/list/get,
cancel and command recovery; seven Artifact operations cover logical artifacts, immutable versions, independently
revocable delivery authorization, and its capability-authenticated byte-stream redemption plane. Delivery authorization
is intentionally a non-idempotent, non-recoverable bearer response with `Cache-Control: no-store`; retry creates a new
grant and receipts never replay it. Redemption returns `application/octet-stream` with bounded RFC 6266/8187 filename
handling and is designed for BFF backpressure rather than JSON/base64 buffering. All list responses use
bounded opaque cursors, and public views contain no provider route, storage locator, secret reference or private owner
digest. The boundary remains `contract-only` until the real Platform provider and Site Web consumer ship together.

Caller intent uses `CanonicalMediaOperationInputV1` deterministic protobuf bytes plus the versioned domain separator
in `spec/media-canonicalization.yaml`. The Node generator validates that manifest against a pinned Buf descriptor set,
then emits pure TypeScript and Python runtimes from one canonical model; the Python entrypoint is only a thin launcher,
not a second copied authority. `corpus/media-canonicalization-v1.json` freezes Unicode, whitespace, revision,
enum, prototype-key, lone-surrogate, normalization-preservation and UTF-8 boundary vectors. The public SHA-256
fingerprint is not Platform's owner-keyed persistence digest and cannot be used as ownership evidence.
`generate-media-canonical.mjs` and `generate_media_canonical.py` validate the same corpus and write only beneath the
system temporary directory; the generated TypeScript helper is the Web/BFF header-injection authority, so callers
never hash ad-hoc JSON. Provider and consumer mirrors are promoted separately by their repository owners.

The same `platform-public@v1` boundary now freezes the personal Saved Memory M0.1 public resources as a contract-only
surface. Its 17 operations cover explicit settings, bounded list/detail/history, remember/correct/restore-as-new,
priority, immediate logical forget/reset, asynchronous import/export, and command recovery. Site, subject, space, and
namespace scope are derived from authenticated workload/user context and never accepted from the browser. Category is
limited to `profile | preference | fact` and never acts as a hidden scope selector. Project Memory remains feature-off
until its distinct membership/operation policy and public intent are frozen. Entry pages carry an owner-issued
`snapshotRef + spaceVersion`; list and revision-history continuations are bound to that pair and fail stale after any public projection mutation. Import/export polling uses an aggregate-local monotonic `statusVersion`, while completed imports also return the exact resulting owner-space version.
Succeeded commands and detail reads expose the committed/observed owner version, allowing Web to replace unbounded
per-entry anti-revival state with one monotonic scope fence. Import references an Asset-owned quarantined version while Platform resolves its owner facts; export exposes
only a non-bearer Artifact authorization request ref that still requires current Site/user reauthorization. Past-chat
search, Temporary Chat, selection, ContextAssembly/ContextActivity, automatic learning, and GA runtime are absent until their owning phases
are promoted.

Session projection effects use a caller-generated command ref plus a dedicated recovery capability. Ambiguous effects
reconcile through `RecoverProjectionCommand`; committed recovery rotates fresh credential envelopes instead of replaying
the original bearer bytes. Direct commands and recovery share one closed `ProjectionCommandResolution`; symbolic CEL
binds each accepted result arm to its recorded command kind, while each direct RPC wrapper independently rejects a receipt
for another command kind. Replacement bindings carry an immutable lineage ref and monotonically increasing lineage
generation. GA remains outside this delivery authority: it consumes opaque Media handles and emits only a stable Media
operation narrative reference; Session joins that reference to Media- and Artifact-owned facts for browser parts.

## Verification

Run `uv run --locked python contract/generate.py --check`, `pnpm --dir contract run buf:lint`,
`pnpm --dir contract run openapi:generate:public`, `node contract/generate-projection-integrity-corpus.mjs --check`,
`node contract/validate-projection-integrity.mjs --validate-corpus`, and
`node scripts/repository/check-generated-contracts.mjs`. Validate the Web release family with
`pnpm --dir contract run web-release:check`; CI compares the current fifteen-contract candidate with the predecessor's
own valid contract set and then freezes every predecessor v1 registry row and schema.
