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
`generate-public-openapi.mjs`, and the generation/check commands documented in [`README.md`](README.md) form the public boundary.

## Callers and dependencies

Platform, Session, Web, and Agent consume committed generated mirrors or declared wire schemas at their own pins.

## Data ownership and events

Contracts describe wire data; they do not own persisted business records or emitted runtime events.

## Runtime and security

Generation is deterministic and temporary check mode must not rewrite child working trees. Sensitive defaults are forbidden.
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

`agent-execution-evidence@v1` is the Agent-owned read-only reconciliation boundary. Its payload is deliberately
business-identity-free: consumers receive run-local lifecycle evidence plus an independent append-only output
sequence with bounded typed payloads. Terminal completed/failed evidence commits the output high watermark and
digest chain. Output sequence numbers never share or advance lifecycle `durable_seq`. It remains `contract-only`
until a live mTLS provider/consumer compatibility probe exists.

ADR-015's image-first foundation publishes five isolated Protobuf bundles without claiming a runtime:
`platform-media-runtime@v1` (GA to Platform Media), `model-image-effect@v1` (Platform Media to Model Gateway),
and `session-media-projection@v1` (Session-owned reservation, pending binding, activation recovery, replacement,
and separate Media/Credit access), plus separate Media-owner and Credit-owner projection recovery bundles.
Durable `MediaProjectionBindingCommitted` must activate a pending binding
before ordinary Media projection events; Media carries only the Credit-owned cost projection ref/version, while
Credit publishes amount/state through its own audience-bound event. All five registered Media/Image/Session event
families (seven registry boundaries including the two durable event planes) remain `contract-only` and absent from runtime compatibility until real providers and official consumers
ship. Recovery requests use command ref plus opaque access only; owner HMACs, original inputs, Provider payloads,
and top-level Generation/Job identities are not part of these contracts.

Projection event identity is split from delivery capability: immutable owner-signed records carry source sequence,
predecessor ref/digest and content; short-TTL Session target handles and owner recovery handles live only in rotating
delivery envelopes. Replaying after refresh keeps the same record ref/digest/signature. Session repairs gaps and
builds shadow generations through separate read-only `GetProjectionHead` / bounded `PullProjectionEvents` Connect
services for Media and Credit; neither owner can read the other's projection facts.

## Verification

Run `uv run --locked python contract/generate.py --check`, `pnpm --dir contract run buf:lint`,
`pnpm --dir contract run openapi:generate:public`, and `node scripts/repository/check-generated-contracts.mjs`.
