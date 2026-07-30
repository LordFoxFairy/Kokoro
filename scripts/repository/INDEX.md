---
architectureIndex: 1
rootId: root.scripts.repository
owners:
  - "@LordFoxFairy"
---

# Federated repository governance

## Responsibilities

Own Root-only exact-pin verification, promotion bill of materials, historical source freezing, generated-mirror checks, compatibility orchestration, and promotion evidence.

## Non-responsibilities

Repository tooling does not own child branches, locks, releases, tags, runtime state, or business databases.

## Public boundary

- `verify-federated-repositories.mjs` validates the exact `.gitmodules` inventory, selected HEAD/index gitlinks, child checkout/origin/clean state, recoverable refs, protocol declarations, and the closed compatibility matrix. Every protocol declaration has an explicit `active` or `contract-only` lifecycle: active roles must be attested by the matrix and required runtime evidence, while contract-only roles must declare both provider and consumer and are forbidden from the matrix.
- `generate-bom.mjs` writes and re-checks `config/repository/bom.json`, the versioned record of one atomic pin promotion: the promotion commit, four exact pins, each repository's independent `recoverableRef`, the declared protocol and contract list, and length-framed SHA-256 digests of the manifest, matrix, committed evidence and the runtime gate that certified the combination. Generation requires runtime evidence whose combination digest, pins and pre/postflight pin verification match the manifest, so BOM authority is transitively bound to the verifier. `--check` regenerates and byte-compares, reusing the recorded promotion commit instead of re-reading HEAD.
- `freeze-snapshots.mjs` is scoped to the single historical source baseline declared by `config/repository/expected-snapshots.json`: tree, tar archive digest, tracked file count and remote archive reachability. It is not a promotion gate, reads only the committed tree, and refuses to reuse a per-repository `recoverableRef` as its shared baseline archive tag. It does not import child source into Root.
- `run-pinned-compatibility.mjs` owns runtime combination evidence. Its closed CLI retains the shared `--infra-env-file` invocation shape but does not open that file or derive a database administrator credential from it. The pinned gate requires PostgreSQL, Redis, MongoDB, MinIO, and LiteLLM; its isolated data leases allocate PostgreSQL, MongoDB, and Redis only. It accepts only code-owned scenario commands and writes sanitized atomic evidence under ignored `tmp/`.
- `check-generated-contracts.mjs` generates each privileged Protobuf-ES boundary and the public Platform OpenAPI boundary in isolated temporary directories, then byte-compares every declared provider and consumer mirror. Check mode never rewrites a child working tree.
- `federated-governance.test.mjs` protects the active documentation authorities from returning to snapshot-import or single-lock topology.

The directory must not import sibling repository source, invoke child Compose files, update branches/tags, or write child databases directly. New compatibility scenarios belong under `scripts/compatibility/`; their machine result contract is closed and human stdout is never treated as evidence.

The `hub-runtime` command demonstrates the intended ownership split: Root orchestrates the published Platform
Hub providers and a thin Platform driver over production projection and signature-verification APIs, seeds only
through the official Admin HTTP API, and delegates runtime assertions to Agent's production client. Root may
compose published child runtime APIs for cross-repository evidence; it must not reimplement product behavior or
write Hub Mongo directly.

Promotion order is fixed: run the verifier and compatibility runner against the same selected tree (`head` or staged `index`), commit the four gitlinks and the manifest atomically, rerun the verifier in `head` mode, then generate the BOM against that commit and commit the BOM separately. A Root manifest may only reference its parent or an earlier commit, so the BOM never carries a field naming the commit that contains it.

The manifest also records future contract ownership without presenting it as released capability. BOM repository
protocol lists intentionally include only `active` declarations; contract-only roles remain bound indirectly by the
manifest digest and cannot appear in the BOM contract/runtime evidence list until lifecycle promotion.

## Callers and dependencies

Root CI and release operators call these commands against the four permanently independent repositories declared by `.gitmodules`.

## Data ownership and events

This component owns repository manifests, the promotion bill of materials, exact pin evidence, and sanitized compatibility results; it owns no application events.

## Runtime and security

Commands use fixed argv, reject secret-shaped output, verify remote refs read-only, and never force-update a branch or tag. The compatibility runner does not open the shared Infra env file, its path never enters evidence, and scenario child environments defensively remove any inherited MySQL root credential.

## Idempotency, failure, and recovery

Read-only verification is repeatable. BOM generation is deterministic: regenerating the same inputs produces byte-identical output, and `--check` fails closed on any drift. Promotion fails closed on pin drift; rollback is a new Root revert followed by recursive verification, then a new BOM against the revert commit.

## Extension rules and forbidden dependencies

New cross-repository scenarios belong under `scripts/compatibility/`. Never import sibling source, invoke child Compose, or accept floating refs.

## Current gotchas

Recoverable tags prove reachability, not hosted immutability, unless separate ruleset evidence exists.

The BOM digests the committed evidence documents as they exist in the working tree, so it must be generated after those documents are final; editing them later makes `--check` fail until the BOM is regenerated. `runtimeGate.evidenceDigest` names a runner artifact under ignored `tmp/`, so `--check` re-derives every other field but can only re-derive that digest when the same evidence file is passed again; `runtimeGate.combinationDigest` is always re-derived from the manifest and matrix, and `generate-bom.test.mjs` guards the shared algorithm against runner drift.

`freeze-snapshots.mjs` remains bound to the historical baseline commits in `expected-snapshots.json`. It is expected to fail against promoted pins; that is the fail-closed signal, not a regression to be silenced by rewriting the baseline or moving tags.

## Verification

Run `node --test scripts/repository/*.test.mjs` and both HEAD/index verifier modes before promotion. After the promotion commit, run `node scripts/repository/generate-bom.mjs --check` to prove the recorded bill of materials still matches the manifest, matrix and evidence.
