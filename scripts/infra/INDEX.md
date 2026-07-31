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

`manager.mjs` is the lifecycle entrypoint, `inventory.mjs` reports/records/checks sanitized Docker identity, and `scope.mjs` leases test partitions. `site-release-image.mjs` is the pure immutable OCI digest syntax policy; `validate-site-release-image.mjs` applies it to a release env without contacting Docker or infra. It also rejects the known `reference-site` repository naming, but cannot identify a renamed fixture or prove artifact provenance. C1 release qualification remains incomplete until a later promotion gate verifies a digest-bound Site release manifest or attestation. `compose-production-assembly.test.mjs` and `production-assembly.test.mjs` prove that Root deployment manifests use real child entrypoints, ports, Dockerfiles, and independent process boundaries; `k8s-session-probes.test.mjs` pins Session's distinct startup, liveness, dependency-readiness, and secure Connect probe semantics. Production composition has no default/reference Site image, and Compose independently rejects a missing or empty input. PostgreSQL is the canonical relational authority for the latest Platform and Session design. MySQL is available only through the explicit `mysql-compat` profile to preserve a local legacy container/volume; it is not selected by default Platform or full lifecycle operations.

## Callers and dependencies

The Root-owned Session probe gate pins Kubernetes wiring: the Pod-only plain-HTTP listener on `3902`, unchanged browser and owner-authority service ports, and absence of `3902` from the Service. Session owns the listener implementation and verifies its route allowlist, browser mTLS, and reuse of aggregate Browser readiness. Cross-repository compatibility evidence is collected only after the Session pin is promoted; Root tests must not inspect an unpromoted submodule worktree.

Root verification and operators call these commands. The four child repositories remain independent and cannot bypass this lifecycle during Root integration.

## Data ownership and events

Infra owns environment-category labels and physical test resources. Services own the records stored inside leased logical partitions.

## Runtime and security

Commands project metadata without container environment values or host mount paths, preserve `shell: false`, and reject business identifiers as Infra scope. Preflight checks exact volume ownership, data markers, and mount users. Running MySQL/PostgreSQL containers are authenticated before mutation; stopped containers are started by Compose first and must then pass the same stdin-only credential probe. Every ensure performs a mandatory post-start database probe before accepting the running postcondition. MinIO requires an explicit matching non-secret auth-generation marker.

## Idempotency, failure, and recovery

Matching-scope stateful or mixed ensure uses `--no-recreate`; ordinary Compose configuration drift cannot replace existing services. Unknown/orphaned target volumes and exact-name/port/mount competing containers fail before mutation. Transitions require a separate receipt-bound activation. Stop/status reject the wrong scope, and prune, destructive volume/image removal, implicit orphan removal, and stateful refresh are denied.

## Extension rules and forbidden dependencies

Add lifecycle behavior only through `manager.mjs` and matching tests. Do not add a second Compose authority or child-source bind mount.

## Current gotchas

The lifecycle environment scope and per-run logical data lease are separate identities. The default `platform` and `full` profiles include PostgreSQL and exclude MySQL; `postgres-transition` remains only as a focused alias and `mysql-compat` must be requested explicitly. A PostgreSQL-only lease does not consume a Redis database. Platform receives distinct `api`, `worker`, `admin`, `migrator`, and `test` identities; Session receives distinct `api`, `worker`, `migrator`, and `test` identities. The Platform `admin` identity is a narrow control-plane credential, not an API/Worker alias. Child migrators own schema-specific grants, and Root grants only CONNECT plus the test-to-migrator setup membership; child migrations own exact schema/table/function privileges.

Volumes created before Task 2A have Compose project/volume ownership labels but no Kokoro data marker. They are accepted only as explicit legacy evidence when exactly one matching-scope canonical container for the exact service mounts the expected volume and that container also lacks the Task 2A profile/data/auth labels. `--no-recreate` deliberately leaves those labels untouched. This exception is not a path for new markerless volumes: orphaned volumes, unknown mount users, incomplete Compose ownership, non-empty wrong markers, or current-format containers with a missing volume marker still fail closed. A legacy MySQL container remains stopped during default ensures; an explicit `mysql-compat` ensure must start it without recreation and pass both root and application credential probes. Legacy MinIO credentials are not authenticated by this path; the unchanged container remains usable, but external credential validation is required before any activation or credential migration.

## Verification

Run `node --test scripts/infra/*.test.mjs`. Use `node scripts/infra/inventory.mjs --record <path>` before a bounded transition, store the emitted checksum in an external immutable authority, then run `--check <path> --expect-digest <sha256:...>` for exact identity verification. The record's self-hash is an integrity checksum, not authorization. Use real Docker only after consumers and rollback gates are ready, then clean up only explicitly owned containers—never volumes, images, or developer data.
