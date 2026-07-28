---
architectureIndex: 1
rootId: root.scripts.infra
owners:
  - "@LordFoxFairy"
---

# Root Infra lifecycle

## Responsibilities

Own the lifecycle authority for the fixed `kokoro-infra` Compose project and bounded test-data leases.

## Non-responsibilities

Infra does not own business Site/tenant/workspace identity, child service deployment, or production secrets.

## Public boundary

`manager.mjs` is the lifecycle entrypoint, `inventory.mjs` reports/records/checks sanitized Docker identity, and `scope.mjs` leases test partitions. PostgreSQL is additive under `postgres-transition`; MySQL remains canonical until a separately reviewed activation.

## Callers and dependencies

Root verification and operators call these commands. The four child repositories remain independent and cannot bypass this lifecycle during Root integration.

## Data ownership and events

Infra owns environment-category labels and physical test resources. Services own the records stored inside leased logical partitions.

## Runtime and security

Commands project metadata without container environment values or host mount paths, preserve `shell: false`, and reject business identifiers as Infra scope. Persistent authenticated services use non-secret auth-generation markers so credential/volume drift fails before mutation.

## Idempotency, failure, and recovery

Matching-scope ensure converges configuration. Generic ensure never force-recreates a mismatched stateful stack; transitions require a separate receipt-bound activation. Stop/status reject the wrong scope, and prune, destructive volume/image removal, implicit orphan removal, and stateful refresh are denied.

## Extension rules and forbidden dependencies

Add lifecycle behavior only through `manager.mjs` and matching tests. Do not add a second Compose authority or child-source bind mount.

## Current gotchas

The lifecycle environment scope and per-run logical data lease are separate identities. Default leases retain MySQL compatibility; callers must request `postgres` explicitly during the additive phase. A PostgreSQL-only lease does not consume a Redis database.

## Verification

Run `node --test scripts/infra/*.test.mjs`. Use `node scripts/infra/inventory.mjs --record <path>` before a bounded transition and `--check <path>` for exact identity verification. Use real Docker only after consumers and rollback gates are ready, then clean up only explicitly owned containers—never volumes, images, or developer data.
