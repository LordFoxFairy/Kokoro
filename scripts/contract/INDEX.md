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
receipt durability, or that a provider actually implements a registered operation.

## Public boundary

`check-boundary-registry.mjs` is the supported entrypoint; `check-boundary-registry.test.mjs` defines its
fail-closed behaviour. Policy data is [`contract/registry/boundaries.yaml`](../../contract/registry/boundaries.yaml),
described by [`contract/registry/boundaries.schema.json`](../../contract/registry/boundaries.schema.json).
The registry is JSON-compatible YAML, following `config/architecture/index-roots.yaml`: the filename the spec
mandates, without adding a YAML parser dependency.

## Callers and dependencies

Root CI and contract owners call the check. It reads `contract/proto/`, `contract/spec/`,
`config/repository/compatibility-matrix.json` and `config/architecture/index-roots.yaml`, and writes nothing.

## Data ownership and events

The registry owns boundary inventory: owner, callers, audience, protocol, deadline, retry class, receipt,
failure owner, and how each operation binds its Site. Wire shapes stay owned by `contract/proto/` and
`contract/spec/`; this directory never becomes a second authority for them.

## Runtime and security

Read-only and deterministic, Node standard library only, no new dependencies and no network. Source paths must
stay repository-relative and are rejected if they escape the repository.

## Idempotency, failure, and recovery

Repeated runs on unchanged inputs produce the same single-line result. Any violation exits nonzero with sorted
`snake_case` codes naming the offending boundary, operation and path.

## Extension rules and forbidden dependencies

Register a new boundary in the same change that introduces it, and keep it in step with the compatibility
matrix. Declare `sourceStatus: "machine-readable"` only with a real contract source behind it; a boundary
with no source in this repository must say `declared-only` and be counted, never claim coverage it does not
have. Allowed retry classes are derived from `kokoro.common.v1.RetryClass`; never hardcode that list here.

## Current gotchas

Two blind spots are recorded rather than hidden, and both appear in every successful run.

`model-gateway` is `declared-only`: it is the LiteLLM OpenAI-compatible face and this repository holds no
contract source for it, so its operations get no orphan check at all. It is the one boundary that can drift
without the gate noticing, which is exactly why the count is printed.

No operation binds its Site as a `request-field` yet. All 46 `site`-scoped operations are `context-header`:
`platform-runtime` sends `x-kokoro-site-id` derived per route, and `session-browser` is pinned to one Site by
the `KOKORO_SITE_ID` process constant rather than by anything on the wire. Both are Wave T3 debt, not settled
design, and both counts must shrink rather than grow.

The `request-field` proof is per request message for proto sources but per file for spec YAML sources,
because a block-mapping section such as `endpoints` declares no fields of its own. Every `deadlineMs` is
`null` because no boundary declares a deadline in code yet; that is a recorded fact, not an implied default.

## Verification

Run `node --test scripts/contract/*.test.mjs` followed by `node scripts/contract/check-boundary-registry.mjs`.
