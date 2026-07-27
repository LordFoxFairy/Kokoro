# Root Infra lifecycle

This directory owns the root authority for the fixed `kokoro-infra` Compose project.

- `manager.mjs` is the only lifecycle entry point. It validates environment-category scopes, projects Docker preflight metadata without container environment values, and converges scope labels plus stateful mount identities.
- `inventory.mjs` reports sanitized Docker inventory and competing Kokoro authorities.
- `scope.mjs` leases bounded test data partitions inside the root Infra services; its run scope is not the Infra lifecycle environment scope.

The four `kokoro-*` child repositories remain independent and must not own, import, or bypass this lifecycle. Site, tenant, workspace, and opaque business identifiers never enter Infra identity. Lifecycle changes require matching tests in this directory and must preserve `shell: false` command execution.
