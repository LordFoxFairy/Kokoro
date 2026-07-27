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

`check-site-scope-planes.mjs` is the supported entrypoint for the companion rule on the Platform side,
with `check-site-scope-planes.test.mjs` defining its fail-closed behaviour. It scans `kokoro-platform`
for repository and service methods that take an isolation key optionally (`siteId`, `ownerId`,
`workspaceId`, `tenantId`) and requires every call that *declines to scope* — omitting the argument or
passing a literal `undefined` — to sit in an admin-plane file. `--source` takes an alternate tree.

Unscoped reads are legitimate: operators list across every Site. They are legitimate only there. The
same method reached from a user-facing route hands one Site's user every Site's rows, and three
fail-opens have already shipped in exactly that shape — a missing isolation value degrading to *no
isolation* rather than a refusal, each documented in a comment as intended. All three were found by
reading, not by a gate, which is why this one exists.

Its blind spot is recorded rather than hidden: a call passing a variable that happens to be undefined
at runtime reads as scoped. The gate proves intent at the callsite, not the value on the wire. It also
fails closed when it finds no declarations at all, because a parser that stopped matching would
otherwise report a clean tree.

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

Run `node --test scripts/architecture/*.test.mjs`, then `node scripts/architecture/check-index-coverage.ts`,
`node scripts/architecture/check-dependencies.ts`, `node scripts/architecture/check-site-scope-planes.mjs`,
and `uv run --locked python scripts/architecture/check_ga_isolation.py`.
