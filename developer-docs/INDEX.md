# Developer portal map

## Ownership

`developer-docs/` owns presentation and verification only. `kokoro-bff` owns the canonical public OpenAPI. Internal owner contracts, database schemas, generated internal DTOs, credentials, and private payloads are outside this portal.

## Entrypoints

- `catalog/contracts.yaml`: immutable source commit, digest, visibility, and generation metadata.
- `docs/`: authored guides and VitePress composition.
- `docs/reference/v1/generated/`: ignored build input produced from the pinned BFF OpenAPI.
- `examples/`: credential-free cURL, TypeScript, and Python programs exercised by local fixtures.
- `scripts/`: deterministic generation and quality gates.
- `tests/`: behavior and architecture tests.

## Extension rules

1. Add or change a public field in the BFF contract first.
2. Update the catalog only after the owner artifact is committed; record the real commit and SHA-256 digest.
3. Generate reference pages rather than handwriting endpoint copies.
4. Add executable examples with fixture-backed tests and conspicuously fake credentials.
5. Run `corepack pnpm check` before committing.
