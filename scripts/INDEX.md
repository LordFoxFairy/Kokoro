# Root scripts

## Responsibilities

Root scripts only verify repository topology, architecture markers and loopback HTTP composition. They do not own,
generate or copy a sibling repository's API contract, SQL schema or generated wire types.

## Public entry points

- `python3 scripts/verify-backend-design.py --manifest-only` verifies Root architecture documentation and Agent boundary markers.
- `python3 scripts/verify-repository-topology.py --allow-missing-active-checkouts` verifies active/archived repository topology and Phase 1 composition.
- `python3 scripts/verify-ten-repository-standard.py` audits Web, BFF, Agent and the six owner repositories. It emits stable
  text by default and machine-readable diagnostics with `--format json`; a non-zero result remains the explicit work queue until
  every repository converges.
- `python3 -m pytest scripts/tests/test_contract_compatibility.py scripts/tests/test_contract_checkpoint.py -q` exercises the
  frozen inventory parser and fail-closed gitlink, commit-blob digest, topology, package-version and checkpoint checks. Exit `0`
  means the focused verifier tests pass.
- `python3 scripts/verify-contract-compatibility.py --inventory verification/contracts/consumer-inventory.json` checks every
  approved call edge and recorded violation against the Root index and child commit blobs. Exit `0` means all edges are active
  with no violations; current `w1d-web-iam-cut` baseline remains intentionally red with exactly eleven declared broken edges
  and no illegal edge, with no schema, gitlink, digest, evidence or version drift.
- `python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1d-web-iam-cut.json` compares the
  complete active/broken/illegal edge ID sets with a frozen checkpoint and runs the compatibility verifier. Exit `0` accepts
  only the checkpoint's declared broken and illegal outcomes; count-preserving ID swaps and any schema, gitlink, digest,
  evidence or version drift fail.
- `python3 scripts/verify-iam-relay-policy.py` verifies the BFF browser-private IAM relay policy against the frozen IAM/BFF
  gitlink commit blobs. It checks owner commit and allowlist/snapshot digests, TS-to-JSON policy drift, and the narrower
  route/method subset without copying IAM-owned protocol source into BFF. Exit `0` proves provenance, not a successful
  OAuth browser flow; the latter requires a separate real HTTP composition smoke.
- `python3 scripts/e2e/run_system_owner_smoke.py --help` is the isolated System/BFF/Agent HTTP acceptance entry.
  It uses separately pinned Node 24/22 source runners, creates random per-owner PostgreSQL databases, uses a System-only
  Redis prefix, and removes only resources registered by this invocation. BFF user models use an explicit fixed-token IAM
  wire stub; server-only runtime manifest remains bound to configured tenant. It does not perform provider inference.
- `python3 scripts/e2e/run_bff_iam_session_smoke.py --help` is the real IAM Nest/PKCE fixture HTTP to BFF source-process
  admission entry. It pins clean IAM/BFF commits and Root gitlinks, creates only its own BFF database, asks the IAM test-owned
  host to manage IAM facts, exercises seven allow/deny/revocation/outage cases, and verifies owned-resource cleanup.
- `python3 scripts/e2e/run_bff_iam_oidc_smoke.py --help` exercises the IAM→BFF native Code+S256 interaction chain;
  it does not prove Web RP login. `bff_owner_schema.py` gives all five Root BFF smokes an application URL fixed to
  `kokoro_bff`; `psql` observations retain the original libpq URL and explicitly qualify owner SQL.
- `bff_iam_admission_stub.py` is only a strict fixed-token wire fixture for unrelated owner smoke regressions; it is not
  evidence of a real IAM dependency. Real IAM evidence comes from the preceding runner.
- `python3 scripts/e2e/run_capability_bff_smoke.py --help` is the isolated Capability/BFF real-build acceptance entry.
  It requires explicit PostgreSQL, Redis and Node 22/24 arguments, starts the frozen child `dist/main.js` files on
  loopback ports, exercises eight BFF-facing Capability cases, and removes only its two exact databases, Redis prefix,
  process groups and temporary logs. The runner owns case assertions and CLI composition;
  `capability_bff_smoke_runtime.py` owns process groups, acknowledgement-loss-safe PostgreSQL/Redis cleanup and the
  bounded loopback readiness fixture. Pre-existing resource identities are preserved and unknown cleanup inventory
  fails closed.
- `python3 scripts/e2e/run_scheduler_bff_smoke.py --help` is the isolated Scheduler/BFF real-process acceptance entry.
  It requires explicit PostgreSQL, Redis DB 7, Node 22 and Go arguments; source-builds the frozen owners; exercises the
  eleven control, reconciliation, callback, replay, tenant-integrity and response-unknown/restart cases; and removes only
  its two exact databases, harness prefix, registered native Scheduler lease keys, process groups and temporary files.
  The runner owns toolchain/build/start/config composition and total cleanup orchestration;
  `scheduler_bff_smoke_cases.py` owns the behaviors/private-owner observations;
  `scheduler_bff_smoke_runtime.py` owns process-group, PostgreSQL and Redis lifecycle; and
  `scheduler_bff_smoke_http.py` owns bounded HTTP fixtures and operation cancellation; the callback response-drop proxy binds
  only a single locally owned loopback or RFC1918 address with an exact /32 allowlist while its BFF upstream remains loopback. The Agent endpoint
  is an owned deterministic receipt stub, not evidence for a real Agent edge.
- `scripts/governance/` owns the profile matrix and focused contract, delivery, repository, TypeScript, Web/BFF/Agent checks.
  These modules inspect structure and declarations only; the full verifier must still execute every repository's real commands.

Each active child repository runs its own `contract:check`, lint, typecheck, test, build and schema gates. Root never substitutes
those local checks with a generated cross-repository mirror.

## Runtime and security

The E2E runners start each independent checkout through its own documented entrypoint. They communicate over loopback HTTP
and disposable infrastructure; they do not import child source, share a database or derive a contract from another repository.

The old `verify-ten-repository-full.sh` and `e2e/run_stage2_owner_health.py` entries are paused: their unsafe shared-state
implementations were removed, leaving only an explicit `VERIFICATION_ENTRY_PAUSED` diagnostic and exit 2. They never
access infrastructure, and old skip/cleanup options no longer apply. Root owns rebuilding an isolated all-repository
orchestrator; execute each child repository's documented gates in the meantime. The System smoke is not an all-repository gate.

## Current Stage 2 HTTP closure

- `uv run --frozen python scripts/e2e/run_stage2_bff_mock.py --evidence /tmp/kokoro-stage2-bff-mock-e2e.json` builds the independent `kokoro-bff` child repository, starts its real HTTP process in deterministic mock mode, and exercises the current Web-facing Business API v1 across auth, projects, GitHub skills, MCP, scheduler, Agent setup, billing, Chat/SSE, sharing and deletion.
- The Stage 2 E2E runner is intentionally transport-only: Root does not import BFF source, copy its store, or share its database. It proves the current cross-repository boundary over loopback HTTP; child repositories remain responsible for their own unit, integration, type, build and CI gates.
- The new System owner smoke tests published configuration selection and tenant isolation through System and BFF,
  then calls System from the Agent's actual HTTP client and model factory mapping. Runtime acceptance remains pending
  until the System production entry is switched and this command succeeds; unit test success is not live evidence.

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
