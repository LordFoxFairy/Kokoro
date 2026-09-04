# Kokoro Developer API portal

This directory owns the static portal composition, guides, navigation, generated reference pipeline, version catalog, examples, and quality gates. The canonical public API schema remains in `kokoro-bff/contract/openapi/v1/openapi.yaml`; this directory never stores an editable copy.

## Prerequisites

- Node.js `22.22.x`
- Corepack with `pnpm@11.25.0`
- A `kokoro-bff` checkout at `../kokoro-bff`, or `KOKORO_BFF_CHECKOUT` pointing to it

## Commands

```bash
corepack pnpm install --frozen-lockfile
corepack pnpm provenance:check
corepack pnpm dev
```

The complete CI-equivalent gate is:

```bash
corepack pnpm ci
```

See [`INDEX.md`](./INDEX.md) for ownership and extension rules.
