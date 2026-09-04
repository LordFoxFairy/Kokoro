# Projects

A project groups shared instruction, tasks, resources, skills, and scheduled work. Project IDs are opaque server values; names and slugs are presentation fields and must not be used to reconstruct an ID.

## Public surface

The v1 contract can list, create, and read projects; update project instruction; inspect instruction revisions and tasks; upload resources; toggle a project skill; and create a project-scoped scheduled task. See the generated [Projects reference](/reference/v1/generated/projects).

Project creation and every project mutation require an `Idempotency-Key`. Reuse the same key only when retrying the same method, canonical path, and request semantics.

## Instruction revisions

Instruction is shared project behavior, not client-local state. The current v1 revision projection contains documented compatibility fields that do not yet follow the portal's preferred RFC 3339 and `snake_case` conventions. Read their exact shape from the generated schema rather than normalizing them speculatively.

## Isolation

The trusted namespace controls visibility. A path project ID chooses a resource inside that context; request body fields and query parameters cannot move a command into another namespace.
