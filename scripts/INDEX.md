# Root scripts

## Responsibilities

`scripts/contract/` contains the Root-owned, deterministic Slice A contract renderer. It converts the reviewed machine manifest into Protobuf and browser OpenAPI sources without network access or business logic.

## Public entry points

- `uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --write` renders the declared source tree atomically.
- The same command with `--check` renders into temporary storage and byte-compares without editing.

## Callers and dependencies

Root contract gates and release preparation call the renderer. It depends only on the committed manifest validator and the locked Python environment. Buf and Redocly validate outputs after rendering; child repositories do not import this package.

## Runtime and security

The renderer reads local reviewed authority, writes only the declared `contract/proto` and `contract/openapi` outputs, follows no symlinks and performs no network calls. Consumer generation is separately owned by `contract/generate.py` and requires an exact clean Root commit.

## Extension rules and forbidden dependencies

Add rendering behavior only when the machine manifest first defines it and a mutation or artifact-parity test fails. Do not add database access, service calls, child-worktree reads, implicit schema inference or hand-maintained protocol defaults.

## Current gotchas

Protobuf source must already be Buf-canonical; `--check` intentionally fails on formatting drift. The first breaking image is immutable and is never regenerated in place.
