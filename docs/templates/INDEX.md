---
architectureIndex: 1
rootId: replace.with.stable.id
owners:
  - "@owner"
---

# Boundary or component name

## Responsibilities

Describe only responsibilities implemented by current code.

## Non-responsibilities

Name adjacent concerns owned elsewhere.

## Public boundary

Name the real exports, routes, commands, protocols, or process entrypoints in backticks — `src/index.ts`, `POST /things`, `module.main`. A boundary INDEX must name at least one, and prose generic enough to read the same for any module is rejected as a duplicate of its twin.

## Callers and dependencies

Identify upstream callers and allowed downstream boundaries.

## Data ownership and events

State persistence ownership, emitted/consumed events, and migration authority.

## Runtime and security

Record external services, configuration, trust boundaries, and sensitive-data constraints.

## Idempotency, failure, and recovery

Describe retry, duplicate, partial-failure, reconcile, rollback, and recovery behavior.

## Extension rules and forbidden dependencies

Explain where new code belongs and which imports or ownership shortcuts are forbidden.

## Current gotchas

Keep only currently valid caveats. Historical evolution belongs in Git or an ADR.

## Verification

List exact focused commands that protect this boundary.
