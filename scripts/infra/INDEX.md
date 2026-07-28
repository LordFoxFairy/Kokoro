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

Commands project metadata without container environment values or host mount paths, preserve `shell: false`, and reject business identifiers as Infra scope. Preflight checks exact volume ownership, data markers, and mount users. Existing MySQL/PostgreSQL credentials are authenticated with secrets sent only on stdin; MinIO requires an explicit matching non-secret auth-generation marker.

## Idempotency, failure, and recovery

Matching-scope stateful or mixed ensure uses `--no-recreate`; ordinary Compose configuration drift cannot replace existing services. Unknown/orphaned target volumes and exact-name/port/mount competing containers fail before mutation. Transitions require a separate receipt-bound activation. Stop/status reject the wrong scope, and prune, destructive volume/image removal, implicit orphan removal, and stateful refresh are denied.

## Extension rules and forbidden dependencies

Add lifecycle behavior only through `manager.mjs` and matching tests. Do not add a second Compose authority or child-source bind mount.

## Current gotchas

The lifecycle environment scope and per-run logical data lease are separate identities. Default leases retain MySQL compatibility; callers must request `postgres` explicitly during the additive phase. A PostgreSQL-only lease does not consume a Redis database.

## Verification

Run `node --test scripts/infra/*.test.mjs`. Use `node scripts/infra/inventory.mjs --record <path>` before a bounded transition, store the emitted checksum in an external immutable authority, then run `--check <path> --expect-digest <sha256:...>` for exact identity verification. The record's self-hash is an integrity checksum, not authorization. Use real Docker only after consumers and rollback gates are ready, then clean up only explicitly owned containers—never volumes, images, or developer data.
