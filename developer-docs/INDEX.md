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

## Publication gates

- The catalog accepts exactly one `kokoro-bff` contract with `public`
  visibility and the canonical v1 source path.
- Architecture checks reject copied OpenAPI, database schemas, internal
  generated DTOs, credential-shaped literals, unapproved Kokoro headers, and
  links into internal owner checkouts.
- Provenance checks bind the working source and immutable Git blob to the same
  catalog digest.
- Reference checks compare two isolated generations byte for byte.
- Example checks validate requests against OpenAPI and execute against local
  credential-free fixtures.
- The production build is followed by route, fragment, and asset link checks.

## Review-line exception

`scripts/lib/reference-generator.mjs` keeps public-contract validation and the
single deterministic Markdown rendering pipeline together so a second renderer
cannot bypass the publication allowlist. It is below the 800-line blocker; a
second contract version or output format is the trigger to split the renderer.

## Extension rules

1. Add or change a public field in the BFF contract first.
2. Update the catalog only after the owner artifact is committed; record the real commit and SHA-256 digest.
3. Generate reference pages rather than handwriting endpoint copies.
4. Add executable examples with fixture-backed tests and conspicuously fake credentials.
5. Run `corepack pnpm check` before committing.
