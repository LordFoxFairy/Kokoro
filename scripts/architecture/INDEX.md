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

`check-service-contract-imports.mjs` is the supported entrypoint for the peer-import rule, with
`check-service-contract-imports.test.mjs` defining its fail-closed behaviour. Each Platform service
exports a package root, which re-exports its services, servers and domain types, and a `./contract`
entry exposing only its HTTP schemas. A peer must bind the second. `--source` takes an alternate tree.

The sibling dependency gate reads `package.json`, where both spellings are the same dependency, so
this can only be enforced at the import site. Importing the root for a two-field response schema
drags the whole service in — `@kokoro/user` alone brings Prisma, Fastify, ioredis, jose and
nodemailer — and it decides how much survives the services being split into separate repositories:
what a peer imports today is what has to be published tomorrow.

Two exemptions, both counted in every successful run rather than hidden. `platform-kit` is the shared
library every service builds on, not a service with a wire contract. And the workspace root is the
composition root, not a peer: a parent that *contains* these packages assembles their module
descriptors into one deployable, which is an implementation relationship with no wire to put a
contract on. That exemption is structural — code outside every child package directory — rather than
a named file, so it cannot be widened by moving a file.

That rule has a companion in `check-dependencies.ts`: an allowance no package under a root uses now
fails. A standing permission nobody exercises would wave through an import nobody reviewed, and it
makes the policy stop describing the architecture it claims to describe. `platform.admin` carried six
such allowances — credit, hub, model, payment, site, user — while importing only `platform-kit`,
because it reaches those modules over HTTP.

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
`node scripts/architecture/check-service-contract-imports.mjs`,
and `uv run --locked python scripts/architecture/check_ga_isolation.py`.

Every check here except the Python one needs no install at all: they read the committed tree with the
Node standard library, and were replayed from a bare recursive clone to confirm it. The Python gate
needs `uv sync --locked` first. Read the exit code directly rather than through a pipe — `cmd | tail`
reports `tail`'s status, which turns a failing gate into a passing one.
