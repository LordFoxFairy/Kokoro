---
architectureIndex: 1
rootId: root.scripts.repository
owners:
  - "@LordFoxFairy"
---

# Federated repository governance

## Responsibilities

Own Root-only exact-pin verification, source freezing, generated-mirror checks, compatibility orchestration, and promotion evidence.

## Non-responsibilities

Repository tooling does not own child branches, locks, releases, tags, runtime state, or business databases.

## Public boundary

- `verify-federated-repositories.mjs` validates the exact `.gitmodules` inventory, selected HEAD/index gitlinks, child checkout/origin/clean state, recoverable refs, protocol declarations, and the closed compatibility matrix.
- `freeze-snapshots.mjs` records recovery provenance for an approved proposed or committed pin set. It does not import child source into Root.
- `run-pinned-compatibility.mjs` owns runtime combination evidence. It accepts only code-owned scenario commands, uses Root Infra and lease-scoped test data, and writes sanitized atomic evidence under ignored `tmp/`.
- `check-generated-contracts.mjs` generates Protobuf-ES output in a temporary directory and byte-compares every declared child mirror. Check mode never rewrites a child working tree.
- `federated-governance.test.mjs` protects the active documentation authorities from returning to snapshot-import or single-lock topology.

The directory must not import sibling repository source, invoke child Compose files, update branches/tags, or write child databases directly. New compatibility scenarios belong under `scripts/compatibility/`; their machine result contract is closed and human stdout is never treated as evidence.

Before promoting gitlinks, run the verifier and compatibility runner against the same selected tree (`head` or staged `index`), then rerun both after the root commit.

## Callers and dependencies

Root CI and release operators call these commands against the four permanently independent repositories declared by `.gitmodules`.

## Data ownership and events

This component owns repository manifests, exact pin evidence, and sanitized compatibility results; it owns no application events.

## Runtime and security

Commands use fixed argv, reject secret-shaped output, verify remote refs read-only, and never force-update a branch or tag.

## Idempotency, failure, and recovery

Read-only verification is repeatable. Promotion fails closed on pin drift; rollback is a new Root revert followed by recursive verification.

## Extension rules and forbidden dependencies

New cross-repository scenarios belong under `scripts/compatibility/`. Never import sibling source, invoke child Compose, or accept floating refs.

## Current gotchas

Recoverable tags prove reachability, not hosted immutability, unless separate ruleset evidence exists.

## Verification

Run `node --test scripts/repository/*.test.mjs` and both HEAD/index verifier modes before promotion.
