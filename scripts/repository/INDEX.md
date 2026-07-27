# Federated repository governance

This directory contains Root-only tooling for the four permanently independent Kokoro repositories.

- `verify-federated-repositories.mjs` validates the exact `.gitmodules` inventory, selected HEAD/index gitlinks, child checkout/origin/clean state, recoverable refs, protocol declarations, and the closed compatibility matrix.
- `freeze-snapshots.mjs` records recovery provenance for an approved proposed or committed pin set. It does not import child source into Root.
- `run-pinned-compatibility.mjs` owns runtime combination evidence. It accepts only code-owned scenario commands, uses Root Infra and lease-scoped test data, and writes sanitized atomic evidence under ignored `tmp/`.
- `federated-governance.test.mjs` protects the active documentation authorities from returning to snapshot-import or single-lock topology.

The directory must not import sibling repository source, invoke child Compose files, update branches/tags, or write child databases directly. New compatibility scenarios belong under `scripts/compatibility/`; their machine result contract is closed and human stdout is never treated as evidence.

Before promoting gitlinks, run the verifier and compatibility runner against the same selected tree (`head` or staged `index`), then rerun both after the root commit.
