# Contract provenance

`catalog/contracts.yaml` is the portal's version catalog. Its sole Phase 1 entry records:

- owner and public visibility;
- semantic contract version;
- source repository and canonical path;
- full source Git commit;
- SHA-256 digest;
- deterministic reference generation command;
- public/internal publication classification.

`pnpm provenance:check` verifies the configured repository origin, recomputes the worktree digest, recomputes the immutable Git blob digest at the pinned commit, checks `info.version`, and rejects uncommitted changes to the canonical source. Unrelated BFF worktree changes are reported as repository state without being misrepresented as contract drift.

`pnpm reference:check` generates the portal reference twice in isolated directories and compares content digests before publishing the ignored build input. No OpenAPI copy is committed to Root.

The exact source commit and digest also appear on every generated reference page.
