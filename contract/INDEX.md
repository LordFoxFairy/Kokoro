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

## Extension rules and forbidden dependencies

Add a schema only with a real producer and consumer. Never create runtime filesystem coupling from a child to this directory.

## Current gotchas

Protobuf sources are authoritative for privileged Connect boundaries; OpenAPI is authoritative for browser/Site public HTTP;
older YAML schemas remain authoritative only for the legacy boundaries that still consume them. Legacy TypeScript mirrors use
the explicit two-argument Zod record form so Zod 3 and Zod 4 consumers remain byte-identical during the toolchain transition.

`AdminCommandService.v2` is a fresh-only maker/checker/worker contract. Browser clients may call only
`SubmitCommand`, `DecideApproval`, and `GetReceipt`; approval queues execution and never
grants a client execution method. Its generated digest helper binds every caller-declared operator generation,
assurance/factor, authentication/step-up instant, and attestation axis to the server-verified transport/session axes.
The removed Prepare/SubmitForApproval/ExecuteApproved authority is intentionally unreachable and has no adapter.

`AdminCommerceService.v1` is the fresh-only typed operator ingress for Commerce catalog and card administration. It exposes a
closed method set—no arbitrary route/action proxy—and binds every effect to Site scope plus the shared authenticated operator
command envelope. `PublishOffer` is one atomic immutable graph publication. Card secrets exist only in the first committed
`IssueCodeBatch` response (maximum 1,000), while replay and all query types expose only delivery-unavailable state, counts and safe
export receipt metadata. Code-batch approval and lifecycle transitions remain Commerce-owned database invariants.

`agent-execution-evidence@v1` is the Agent-owned read-only reconciliation boundary. Its payload is deliberately
business-identity-free: consumers receive only run-local durable sequence/event facts and the canonical Agent
owner payload. It remains `contract-only` until a live mTLS provider/consumer compatibility probe exists.

## Verification

Run `uv run --locked python contract/generate.py --check`, `pnpm --dir contract run buf:lint`,
`pnpm --dir contract run openapi:generate:public`, and `node scripts/repository/check-generated-contracts.mjs`.
