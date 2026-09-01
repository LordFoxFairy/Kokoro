# Root scripts

## Responsibilities

`scripts/contract/` contains the Root-owned, deterministic Slice A contract renderer. It converts the reviewed machine manifest into Protobuf and browser OpenAPI sources without network access or business logic.

## Public entry points

- `uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --write` renders the declared source tree atomically.
- The same command with `--check` renders into temporary storage and byte-compares without editing.
- `python3 scripts/goal2/mock_cross_repository_closure.py` checks the seven Phase 2 owner documents and the Root wire registry without importing child code or sharing databases.
- `python3 scripts/verify-backend-design.py` verifies the backend-design manifest, documented Agent source topology, target architecture markers, legacy-document routing, and local relative links.
- `python3 scripts/verify-repository-topology.py` verifies the ten active local repository remotes, archived-directory removal, Phase 1 storage boundary, and Goal 2 seven-repository manifest.

## Callers and dependencies

Root contract gates and release preparation call the renderer. It depends only on the committed manifest validator and the locked Python environment. Buf and Redocly validate outputs after rendering; child repositories do not import this package.

`verify-backend-design.py` is a documentation gate: it reads only the root handbook and local source-tree paths. It has no network, database, or child-runtime dependency.

## Runtime and security

The renderer reads local reviewed authority, writes only the declared `contract/proto` and `contract/openapi` outputs, follows no symlinks and performs no network calls. Consumer generation is separately owned by `contract/generate.py` and requires an exact clean Root commit.

## Extension rules and forbidden dependencies

Add rendering behavior only when the machine manifest first defines it and a mutation or artifact-parity test fails. Do not add database access, service calls, child-worktree reads, implicit schema inference or hand-maintained protocol defaults.

## Current gotchas

Protobuf source must already be Buf-canonical; `--check` intentionally fails on formatting drift. The active Stage 2 v1 breaking image is frozen after the finalized repository topology. Any future intentional contract reset must archive the previous image outside Root and record the reset in the closure report; ordinary additive changes must pass against the committed image.

## Current Stage 2 HTTP closure

- `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` builds the independent `kokoro-bff` child repository, starts its real HTTP process in deterministic mock mode, and exercises the current Web-facing Business API v1 across auth, projects, GitHub skills, MCP, scheduler, Agent setup, billing, Chat/SSE, sharing and deletion.
- The Stage 2 E2E runner is intentionally transport-only: Root does not import BFF source, copy its store, or share its database. It proves the current cross-repository boundary over loopback HTTP; child repositories remain responsible for their own unit, integration, type, build and CI gates.
- `uv run --frozen python scripts/e2e/run_stage2_owner_health.py` uses disposable PostgreSQL + Redis, starts Web, BFF live, Agent, Scheduler and the six HTTP owners, verifies health/readiness, then cleans up temporary processes, containers and object files while saving `docs/reports/2026-09-01-stage2-owner-health.json`.
- The owner health runner is orchestration only: it starts each independent checkout with that repository's own command and adapter configuration. Root does not copy service source or share business tables; Model is checked through its existing HTTP endpoint.

## Archived historical fixtures

The retired Root deployment and verification entrypoints were removed from this directory and moved to
`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro-archive-2026-09-01/root-legacy/`. This includes the old split Compose files, k8s tree, legacy
provisioning and storage templates, plus `closure-up.py`, `e2e-v21-gate.py`, `chaos-verify.py`,
`trace-verify.py`, `real-model-verify.py`, `verify-all.py`, `generate-model-openrouter-init.py` and their
`procutil.py` helper. They depend on the retired MySQL/Mongo/Session/Platform topology and must not be used
as current contract, Phase 1, or cross-repository validation.

The former native Slice A runner and its PostgreSQL/Redis/LiteLLM/Session-era process supervisor were removed from the active Root because they targeted the retired integrated topology. The complete source and tests are preserved outside the checkout at
`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro-archive-2026-09-01/root-legacy/phase1-native-slice-a/` for historical review only. They must not be used as Stage 2 acceptance evidence.

`ops/langfuse/docker-compose.yml` and `ops/langfuse/.env.local.example` remain archived historical fixtures
for an optional external observability stack; they are not Root deployment dependencies and do not restore the
removed infrastructure Compose entry.
