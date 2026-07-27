---
architectureIndex: 1
rootId: root.superproject
owners:
  - "@LordFoxFairy"
---

# Kokoro Superproject

## Responsibilities

Own cross-repository contracts, exact submodule pins, root Infra orchestration, compatibility evidence, BOM promotion, and architecture governance.

## Non-responsibilities

Root does not own child service source, locks, migrations, releases, runtime state, or private databases.

## Public boundary

The public governance entrypoints are [`README.md`](README.md), [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md), the [`contract`](contract/INDEX.md) tree, and Root-owned scripts.

## Callers and dependencies

CI and release operators call Root tooling. Root invokes child public commands at exact gitlink pins and never imports sibling source.

## Data ownership and events

Root owns manifests and sanitized evidence under `config/` and ignored `tmp/`; business records and runtime events remain child-owned.

## Runtime and security

Root Infra is the single local lifecycle authority. Commands use fixed argv, scoped test resources, and never print credentials.

## Idempotency, failure, and recovery

Pin promotion is atomic. Failed combinations remain unpromoted; rollback creates a new revert commit to a previously verified pin set.

## Extension rules and forbidden dependencies

Add cross-repository IDL under `contract/` and root-only automation under `scripts/`. Never add sibling source imports, floating branch pins, or child dependencies to the Root lock.

## Current gotchas

The production delivery program is active. Passing the Admin Auth pilot does not mean Wave 0 or later product waves are complete.

## Verification

Run `node --test scripts/architecture/*.test.mjs`, both architecture check entrypoints, repository governance tests, contract tests, then the pinned compatibility gate at promotion time.
