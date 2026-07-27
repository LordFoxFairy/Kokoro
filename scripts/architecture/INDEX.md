---
architectureIndex: 1
rootId: root.scripts.architecture
owners:
  - "@LordFoxFairy"
---

# Architecture governance

## Responsibilities

Validate registered architecture roots, current-fact INDEX files, public boundaries, and allowed dependency direction.

## Non-responsibilities

Static architecture checks do not prove remote protocol behavior, runtime authorization, database isolation, or deployment health.

## Public boundary

`check-index-coverage.ts` and `check-dependencies.ts` are the supported policy entrypoints; their tests define fail-closed behavior.


`check_ga_isolation.py` is the supported entrypoint for the GA runtime's isolation rule, with
`test_check_ga_isolation.py` defining its fail-closed behaviour. It scans `kokoro-agent/src` and rejects
any of the eight Platform identity axes (`site_id`/`siteId`, `owner_id`/`ownerId`,
`workspace_id`/`workspaceId`, `user_id`/`userId`) as well as a namespace composed from a business
prefix such as `user:`. `--source` takes an alternate tree for fixtures.

GA is not a Platform module and must not become one: `namespace` is its only isolation key and stays
opaque, while `siteId` is resolved and enforced entirely on the Platform side. The rule was documented
in the codebase map but nothing checked it, so this gate freezes the currently-clean state — an empty
scan fails rather than reading as clean.

## Callers and dependencies

Root CI and module owners call these checks. Policy is read from `config/architecture/index-roots.yaml`.

## Data ownership and events

The manifest owns architecture inventory. INDEX files explain current semantics and contain no mutable runtime state.

## Runtime and security

Paths must remain repository-relative, command declarations are argv arrays, and ignored/generated trees cannot become accidental roots.

## Idempotency, failure, and recovery

Checks are read-only and deterministic. Invalid or incomplete inventory exits nonzero with bounded diagnostics.

## Extension rules and forbidden dependencies

Register new public roots in the same change. Do not add broad or permanent exemptions, shell commands, or target-state claims before code exists.

## Current gotchas

The checker consumes JSON-compatible YAML to avoid adding a Root runtime dependency solely for policy parsing.

## Verification

Run `node --test scripts/architecture/*.test.mjs` followed by both architecture check entrypoints.
