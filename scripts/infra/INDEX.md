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

`manager.mjs` is the lifecycle entrypoint, `inventory.mjs` reports sanitized Docker ownership, and `scope.mjs` leases test partitions.

## Callers and dependencies

Root verification and operators call these commands. The four child repositories remain independent and cannot bypass this lifecycle during Root integration.

## Data ownership and events

Infra owns environment-category labels and physical test resources. Services own the records stored inside leased logical partitions.

## Runtime and security

Commands project metadata without container environment values, preserve `shell: false`, and reject business identifiers as Infra scope.

## Idempotency, failure, and recovery

Matching-scope ensure converges configuration. Scope transitions require full-set recreation; stop/status reject the wrong scope and volumes are not implicitly deleted.

## Extension rules and forbidden dependencies

Add lifecycle behavior only through `manager.mjs` and matching tests. Do not add a second Compose authority or child-source bind mount.

## Current gotchas

The lifecycle environment scope and per-run logical data lease are separate identities.

## Verification

Run `node --test scripts/infra/*.test.mjs`; use real Docker only once at promotion and clean up owned containers afterward.
