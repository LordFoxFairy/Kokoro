# Root scripts

## Responsibilities

Root scripts only verify repository topology, architecture markers and loopback HTTP composition. They do not own,
generate or copy a sibling repository's API contract, SQL schema or generated wire types.

## Public entry points

- `python3 scripts/verify-backend-design.py --manifest-only` verifies Root architecture documentation and Agent boundary markers.
- `python3 scripts/verify-repository-topology.py --allow-missing-active-checkouts` verifies active/archived repository topology and Phase 1 composition.
- `python3 scripts/verify-seven-repository-standard.py` audits the seven owner repositories when their local checkouts are present.

Each active child repository runs its own `contract:check`, lint, typecheck, test, build and schema gates. Root never substitutes
those local checks with a generated cross-repository mirror.

## Runtime and security

The E2E runners start each independent checkout through its own documented entrypoint. They communicate over loopback HTTP
and disposable infrastructure; they do not import child source, share a database or derive a contract from another repository.

## Current Stage 2 HTTP closure

- `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` builds the independent `kokoro-bff` child repository, starts its real HTTP process in deterministic mock mode, and exercises the current Web-facing Business API v1 across auth, projects, GitHub skills, MCP, scheduler, Agent setup, billing, Chat/SSE, sharing and deletion.
- The Stage 2 E2E runner is intentionally transport-only: Root does not import BFF source, copy its store, or share its database. It proves the current cross-repository boundary over loopback HTTP; child repositories remain responsible for their own unit, integration, type, build and CI gates.
- `uv run --frozen python scripts/e2e/run_stage2_owner_health.py` uses disposable PostgreSQL + Redis, starts Web, BFF live, Agent, Scheduler and the six HTTP owners, verifies health/readiness, then cleans up temporary processes, containers and object files while saving `docs/reports/2026-09-01-stage2-owner-health.json`.
- The owner health runner is orchestration only: it starts each independent checkout with that repository's own command and adapter configuration. Root does not copy service source or share business tables; Model is checked through its existing HTTP endpoint.

## Archived historical fixtures

The retired Root deployment and verification entrypoints were removed from this directory and from the local
workspace. GitHub history remains available in the archived repositories; the old split Compose files, k8s tree,
legacy provisioning and storage templates, plus `closure-up.py`, `e2e-v21-gate.py`, `chaos-verify.py`,
`trace-verify.py`, `real-model-verify.py`, `verify-all.py`, `generate-model-openrouter-init.py` and their
`procutil.py` helper depend on the retired MySQL/Mongo/Session/Platform topology and must not be used as current
contract, Phase 1, or cross-repository validation.

The former native Slice A runner and its PostgreSQL/Redis/LiteLLM/Session-era process supervisor were removed from
the active Root because they targeted the retired integrated topology. Their source remains in Git history only and
must not be used as Stage 2 acceptance evidence.

`ops/langfuse/docker-compose.yml` and `ops/langfuse/.env.local.example` remain archived historical fixtures
for an optional external observability stack; they are not Root deployment dependencies and do not restore the
removed infrastructure Compose entry.
