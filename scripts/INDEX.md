---
architectureIndex: 1
rootId: root.scripts
owners:
  - "@LordFoxFairy"
---

# Root automation

## Responsibilities

Own Root-only repository governance, Infra lifecycle, compatibility, architecture checks, and release evidence automation.

## Non-responsibilities

Scripts do not implement product behavior, replace child CI, or write another service's private database.

## Public boundary

The supported command families are documented by the adjacent component INDEX files for [`architecture`](architecture/INDEX.md), [`compatibility`](compatibility/INDEX.md), [`infra`](infra/INDEX.md), and [`repository`](repository/INDEX.md).

## Callers and dependencies

Developers and Root CI call these commands from the superproject root against exact child pins.

## Data ownership and events

Scripts may write sanitized evidence under ignored `tmp/`; durable business data and runtime event streams are out of scope.

## Runtime and security

Use fixed argv arrays, bounded timeouts, explicit resource leases, and redacted machine results. Do not evaluate manifest-provided shell strings.

## Idempotency, failure, and recovery

Read-only checks are repeatable. Mutating Infra commands converge scoped resources and clean up owned processes in `finally` paths.

## Extension rules and forbidden dependencies

Place a command in the narrowest component. Do not import child source or introduce a second Infra lifecycle authority.

## Current gotchas

Full runtime verification requires Root Infra. Unit and static gates must remain runnable without starting Docker.

## Verification

Run `node --test scripts/architecture/*.test.mjs scripts/repository/*.test.mjs scripts/infra/*.test.mjs` and the Python compatibility tests relevant to the change.
