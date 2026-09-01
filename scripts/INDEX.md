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

Protobuf source must already be Buf-canonical; `--check` intentionally fails on formatting drift. The first breaking image is immutable and is never regenerated in place.

## Native Slice A backend gate

- `uv run --frozen python scripts/e2e/run_slice_a_native.py` creates private secrets and fixture roots, boots a fresh native PostgreSQL 18 cluster, native Redis, the five pinned backend candidates, LiteLLM and the deterministic OpenAI-compatible fixture, then exercises login → Chat → Agent/HITL → restart recovery → session lifecycle.
- `uv run --frozen python scripts/e2e/run_slice_a_native.py --compare-evidence RUN1.json RUN2.json` validates both release-evidence schemas and compares the exact catalog, baseline, seed, Model bootstrap and retention watermark/tail facts from two fresh runs.
- `uv run --frozen pytest scripts/tests/test_slice_a_native.py scripts/tests/test_openai_slice_a_fixture.py scripts/tests/test_slice_a_backend_runner.py -q` covers the local lifecycle, fixture wire protocol, digest parity, guarded cleanup and bounded runner behavior without Docker.
- `scripts/slice_a/native.py` is the owned process supervisor. `create_secrets.py`, `create_fixture_dir.py`, `seed.py`, `wait_ready.py`, `guardian.py` and `cleanup.py` are deliberately narrow lifecycle helpers; none owns business state.

The gate accepts only exact clean candidate commit/tree pairs, a byte-identical committed generated-client closure and a committed Root SQL baseline. Site is a Web fixture context and SQL seed, not a runtime process; an exact-candidate source assertion rejects `site_site` access outside IAM runtime source. Site/Model deployment seed may use the provisioning owner before runtime; login, RBAC, Chat and Agent state must cross their generated service contracts. Child runtime database URLs carry no `search_path` override, and the gate never installs IAM permissions through SQL. The product gate does use the provisioning owner to suspend/restore the local Site and expire local stream rows so it can prove IAM suspension and production `SNAPSHOT_REQUIRED` → snapshot watermark → contiguous new-tail recovery.

Every child is launched in a dedicated recorded session/process group behind a pre-exec persistence gate. Supervisor, guardian and outer runner cleanup use high-precision process identities, drain every owned group, verify every owned port and redact captured diagnostics before a PASS or evidence file can be emitted.

## Archived historical fixtures

The retired Root deployment and verification entrypoints were removed from this directory and moved to
`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro-archive-2026-09-01/root-legacy/`. This includes the old split Compose files, k8s tree, legacy
provisioning and storage templates, plus `closure-up.py`, `e2e-v21-gate.py`, `chaos-verify.py`,
`trace-verify.py`, `real-model-verify.py`, `verify-all.py`, `generate-model-openrouter-init.py` and their
`procutil.py` helper. They depend on the retired MySQL/Mongo/Session/Platform topology and must not be used
as current contract, Phase 1, or cross-repository validation.

`ops/langfuse/docker-compose.yml` and `ops/langfuse/.env.local.example` remain archived historical fixtures
for an optional external observability stack; they are not Root deployment dependencies and do not restore the
removed infrastructure Compose entry.
