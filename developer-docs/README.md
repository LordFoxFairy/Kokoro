# Kokoro Developer API portal

This directory owns the static portal composition, guides, navigation, generated reference pipeline, version catalog, examples, and quality gates. The canonical public API schema remains in `kokoro-bff/contract/openapi/v1/openapi.yaml`; this directory never stores an editable copy.

## Prerequisites

- Node.js `22.22.x`
- Corepack with `pnpm@11.25.0`
- A `kokoro-bff` checkout at `../kokoro-bff`, or `KOKORO_BFF_CHECKOUT` pointing to it

## Commands

| Command | Purpose |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | Install the exact dependency graph. |
| `corepack pnpm dev` | Generate reference input and start the local portal. |
| `corepack pnpm build` | Generate reference input and produce the static site. |
| `corepack pnpm lint` | Check JavaScript, TypeScript, and Markdown style. |
| `corepack pnpm typecheck` | Type-check portal configuration and examples. |
| `corepack pnpm test` | Run verifier, generator, example, architecture, and link unit tests. |
| `corepack pnpm provenance:check` | Verify the canonical Git blob, worktree file, version, and digest. |
| `corepack pnpm reference:generate` | Materialize ignored reference pages from the pinned BFF OpenAPI. |
| `corepack pnpm reference:check` | Prove reference generation is deterministic. |
| `corepack pnpm examples:check` | Validate and run every manifest example against local fixtures. |
| `corepack pnpm architecture:check` | Enforce publication boundaries and the public contract allowlist. |
| `corepack pnpm links:check` | Check built internal routes, fragments, and assets. |
| `corepack pnpm preview` | Preview an already-built static site. |

The complete CI-equivalent gate is:

```bash
corepack pnpm run ci
```

The CI entrypoint performs lint, type checking, unit tests, provenance and
determinism checks, executable examples, architecture policy, a production
build, and built-site link validation in that order.

See [`INDEX.md`](./INDEX.md) for ownership and extension rules.
