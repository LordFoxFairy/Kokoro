# Slice A Root Database and Contracts Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before a lane starts, its next milestone MUST be expanded into a separately reviewed JIT implementation cut with exact files, actual RED test/code, self-contained commands and one precise commit; workers never invent omitted code from this roadmap.

**Goal:** Produce the exact Slice A PostgreSQL 18 baseline, owner inventory, owner-scoped Prisma schemas, Protobuf service contracts and browser-facing OpenAPI used by every candidate repository.

**Architecture:** Root SQL is the only DDL authority. SQL segments compose deterministically into `database/baseline/kokoro.sql`; live PostgreSQL catalog inspection verifies the 50+4 manifest and constraints. Buf generates consumer-specific TypeScript/Python artifacts from one frozen Root contract commit.

**Tech Stack:** PostgreSQL 18, `pgcrypto`, SQL, Python 3.11 tooling, psycopg 3.3.4, pytest, LangGraph checkpoint-postgres 3.1.0, Buf CLI, Protobuf-ES, grpcio-tools.

## Global Constraints

- Implement only Slice A tables from canonical data model §0.2.
- Use single-column UUID primary keys for owner business tables; the pinned LangGraph tables retain their official keys.
- Install no `chat_share`, Skill/MCP item/catalog, Storage, Entitlement or Payment table.
- Every cross-axis relation has an executable composite FK or deferred constraint trigger, not an application-only comment.
- Every current/live pointer rejects draft revisions in PostgreSQL.
- Baseline generation is deterministic and refuses dirty or uncommitted source input.
- Child Prisma schemas contain only owned models and never carry migration blocks.

## Parallel Scheduling

The reviewed contract barrier roadmap is the only shared barrier. After its clean contract-source commit and separate Root E2E descendant-output commit:

- Milestones 1–4 build the owner SQL segments in the Root database lane while Chat/Agent/owner lanes port domain tests against the already-frozen descriptors.
- Milestone 5 waits for the committed composed baseline. Consumer generation is already owned by the completed contract barrier/output cuts and is not rerun here; final checks verify each runtime consumer explicitly, while contract tests retain the frozen registry verbatim. The master roadmap's structured retirement boundary governs its compatibility exception.

This ordering keeps one contract source while avoiding a false requirement that all SQL implementation finish before child domain/RPC work begins.

---

### Milestone 1: Lock the Slice A manifest and SQL segment order

**Files:**
- Create the isolated database toolchain: `database/pyproject.toml`, `database/uv.lock`, `database/package.json`, `database/pnpm-lock.yaml`, `database/pnpm-workspace.yaml`, `database/.gitignore`
- Create: `database/slices/slice-a.json`
- Create: `database/schema/00-foundation.sql`
- Create: `database/tests/test_slice_a_manifest.py`
- Create: `scripts/database/compose_baseline.py`
- Create: `scripts/database/__init__.py`

**Interfaces:**
- Consumes: canonical data model §0.2.
- Produces: `compose_baseline(root: Path, slice_name: str) -> bytes` and the exact table allowlist.

**JIT cut requirement 1 — Create an isolated database toolchain without changing the frozen contract toolchain**

The prerequisite contract barrier owns the Root Python/Node locks and they remain byte-unchanged. Database work uses its own exact project under `database/`: Python `>=3.11,<3.14`, `pytest==8.4.2`, `psycopg[binary]==3.3.4`, `langgraph-checkpoint-postgres==3.1.0`, plus database-local `prisma@6.19.3`. No dependency uses a range. Child repositories still never run migrations.

```bash
uv lock --project database --check
uv sync --project database --frozen
pnpm --dir database install --frozen-lockfile
uv run --frozen python contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
uv run --isolated --project database --frozen pytest --version
pnpm --dir database exec prisma --version
```

Commit the isolated database locks with the Slice A SQL manifest; the Root contract locks remain unchanged.

**JIT cut requirement 2 — Write the failing manifest test**

```python
EXPECTED_COUNTS = {
    "site": 2,
    "iam": 14,
    "chat": 14,
    "agent": 13,
    "capability": 2,
    "model": 5,
    "langgraph": 4,
}

def test_slice_a_manifest_is_exact() -> None:
    manifest = json.loads(Path("database/slices/slice-a.json").read_text())
    assert manifest["schema"] == "kokoro"
    assert manifest["ownerTableCount"] == 50
    assert manifest["checkpointerTableCount"] == 4
    assert {owner: len(names) for owner, names in manifest["tables"].items()} == EXPECTED_COUNTS
    assert "chat_share" not in json.dumps(manifest)
    assert "capability_runtime_snapshot_item" not in json.dumps(manifest)
```

**JIT cut requirement 3 — Run the test and observe RED**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_slice_a_manifest.py -q
```

Expected: failure because `database/slices/slice-a.json` is absent.

**JIT cut requirement 4 — Add the exact manifest**

The JSON keys and arrays are fixed:

```json
{
  "version": 1,
  "slice": "slice-a",
  "schema": "kokoro",
  "segments": ["00-foundation", "10-site", "20-iam", "30-chat", "40-agent", "45-langgraph-checkpointer", "50-capability", "60-model", "99-cross-capability-relations"],
  "ownerTableCount": 50,
  "checkpointerTableCount": 4,
  "tables": {
    "site": ["site_site", "site_domain"],
    "iam": ["iam_principal", "iam_user", "iam_identity", "iam_contact", "iam_magic_link", "iam_auth_session", "iam_command_receipt", "iam_organization", "iam_membership", "iam_role", "iam_permission", "iam_role_permission", "iam_membership_role", "iam_security_event"],
    "chat": ["chat_conversation", "chat_message", "chat_message_part", "chat_command_receipt", "chat_run_launch", "chat_active_run", "chat_run_view", "chat_interaction", "chat_control_command", "chat_control_outbox", "chat_launch_outbox", "chat_projection_inbox", "chat_projection_dlq", "chat_stream_event"],
    "agent": ["agent_run", "agent_execution_manifest", "agent_run_lease", "agent_control_inbox", "agent_event_outbox", "agent_dispatch_outbox", "agent_projection_ack", "agent_tool_effect", "agent_run_usage", "agent_run_usage_line", "agent_sandbox_binding", "agent_memory", "agent_dispatch_dlq"],
    "capability": ["capability_runtime_snapshot", "capability_command_receipt"],
    "model": ["model_provider", "model_definition", "model_revision", "model_routing_policy", "model_provider_health_state"],
    "langgraph": ["checkpoints", "checkpoint_blobs", "checkpoint_writes", "checkpoint_migrations"]
  }
}
```

**JIT cut requirement 5 — Implement deterministic composition**

`compose_baseline.py` must normalize LF, prepend source SHA-256 comments, reject symlinks and concatenate only manifest segments. The public function is:

Expose the concrete callable `compose_baseline(root: Path, slice_name: str = "slice-a") -> bytes`; it loads the checked manifest, rejects any missing/extra/symlink segment, normalizes LF, prepends each segment's SHA-256 header and returns the concatenated bytes.

The CLI requires exactly one mode, `--write` or `--check`, and accepts the orthogonal release modifier `--require-clean`. `--require-clean` rejects a dirty Root or any segment not readable from the current committed tree before composing; `--write` writes `database/baseline/kokoro.sql` and `database/baseline/manifest.json` atomically.

**JIT cut requirement 6 — Run GREEN and commit**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_slice_a_manifest.py -q
git add database/.gitignore database/pyproject.toml database/uv.lock \
  database/package.json database/pnpm-lock.yaml database/pnpm-workspace.yaml \
  database/slices database/schema/00-foundation.sql \
  database/tests/test_slice_a_manifest.py scripts/database
git commit -m "test(database): lock Slice A manifest"
```

Do not compose the production baseline yet: the checked manifest intentionally rejects missing later segments. Tasks 2 and 3 apply their explicit segment prefix in tests; Task 4 is the first point at which every manifest segment exists and composition may succeed.

### Milestone 2: Implement Site and IAM SQL with tenant constraints

**Files:**
- Create: `database/schema/10-site.sql`
- Create: `database/schema/20-iam.sql`
- Create: `database/tests/test_site_iam_pg18.py`
- Create: `database/tests/pg18.py`

**Interfaces:**
- Consumes: manifest from Task 1.
- Produces: Site/IAM tables and `apply_sql(database_url: str, sql: bytes) -> None` test helper.

**JIT cut requirement 1 — Write PG18 negative tests before DDL**

Implement these tests with real SQL and row-count assertions:

- Insert a membership whose principal and organization belong to different Sites; commit must raise the named tenant constraint and leave no membership row.
- Bind an organization role to a membership from another organization; commit must fail and preserve the original role set.
- Insert a Site auth session for a control-plane operator, then the inverse; each deferred scope trigger must fail at commit.
- Race two transactions creating a personal organization for the same `(site_id, principal_id)`; exactly one commits and the loser reads the winner.
- Claim one IAM command receipt twice with the same digest and once with a different digest; same digest returns the stored result, drift raises conflict and creates no second effect.

`pg18` locates local PostgreSQL 18 binaries, initializes an isolated temporary cluster, applies the requested
segment prefix and fails loudly before setup if the binaries are missing or not version 18.

**JIT cut requirement 2 — Run RED**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_site_iam_pg18.py -q
```

Expected: missing table failures.

**JIT cut requirement 3 — Implement `10-site.sql` and `20-iam.sql`**

Required candidate keys include:

```sql
UNIQUE (principal_id, site_id);
UNIQUE (organization_id, site_id);
UNIQUE (membership_id, organization_id);
UNIQUE (role_id, site_id);
UNIQUE (role_id, organization_id);
```

`iam_identity`, `iam_contact` and `iam_auth_session` use a `DEFERRABLE INITIALLY DEFERRED` trigger that loads `iam_principal` and rejects any mismatch in `principal_scope` or `site_id`, including the `NULL` control-plane branch. The auth-session branch additionally rejects a Site session whose `organization_id` is absent, belongs to another Site, or lacks an active membership for the principal; a control-plane session rejects non-null organization. PostgreSQL tests lock immutable monotonic `family_generation`, `UNIQUE(family_ref,family_generation)`, and show that a disabled permission grants nothing even while its role-binding rows remain present.

**JIT cut requirement 4 — Run GREEN and commit**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_slice_a_manifest.py database/tests/test_site_iam_pg18.py -q
git add database/schema/10-site.sql database/schema/20-iam.sql database/tests
git commit -m "feat(database): add Site and IAM owner schema"
```

`test_site_iam_pg18.py` applies exactly `00-foundation`, `10-site` and `20-iam`; it does not call the full-manifest composer.

### Milestone 3: Implement Chat SQL and concurrency invariants

**Files:**
- Create: `database/schema/30-chat.sql`
- Create: `database/tests/test_chat_pg18.py`

**Interfaces:**
- Produces: the 14 Chat tables and exact cross-tenant/run constraints used by `kokoro-chat`.

**JIT cut requirement 1 — Write failing live tests**

Implement these tests with committed PostgreSQL facts:

- A message parent from another Conversation is rejected by the composite FK.
- RunLaunch user/assistant message references from another Conversation are rejected.
- Two serializable connections competing for one Conversation active slot yield one committed row and one typed conflict.
- The same command ID can exist in different organizations; within one organization same digest replays and drift conflicts.
- Two concurrent stream allocations produce distinct consecutive sequence values with no gap caused by rollback.
- After deleting every stream row at or below a captured watermark, Message/Part/RunView/Interaction owner rows still reconstruct the same snapshot.
- A DecideInteraction receipt for Conversation A bound to an Interaction from Conversation B is rejected both within one organization and across organizations; no control/outbox row survives.

**JIT cut requirement 2 — Run RED**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_chat_pg18.py -q
```

Expected: every case fails with `UndefinedTable` for the first referenced `chat_*` relation.

**JIT cut requirement 3 — Implement `30-chat.sql`**

The PG fixture applies exactly the committed segment prefix through `30-chat`; full baseline composition remains forbidden until Task 4.

Critical keys:

```sql
UNIQUE (conversation_id, organization_id);
UNIQUE (conversation_id, site_id);
UNIQUE (message_id, conversation_id);
UNIQUE (launch_id, conversation_id);
UNIQUE (organization_id, command_id);
UNIQUE (conversation_id, seq);
UNIQUE (conversation_id, event_id);
```

**JIT cut requirement 4 — Run GREEN and commit**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_chat_pg18.py -q
git add database/schema/30-chat.sql database/tests/test_chat_pg18.py
git commit -m "feat(database): add Chat owner schema"
```

### Milestone 4: Implement Agent, empty Capability and Model SQL

**Files:**
- Create: `database/schema/40-agent.sql`
- Create: `database/schema/45-langgraph-checkpointer.sql`
- Create: `database/schema/50-capability.sql`
- Create: `database/schema/60-model.sql`
- Create: `database/schema/99-cross-capability-relations.sql`
- Create: `database/vendor/langgraph-checkpoint-postgres-3.1.0.sql`
- Create: `database/tests/test_agent_control_native_pg18.py`
- Create: `scripts/database/run_in_fresh_pg18_native.py`, `database/tests/test_fresh_pg18_native_runner.py`

**Interfaces:**
- Produces: two-stage Agent admission schema, empty snapshot header, published-only Model routing and the official checkpointer DDL.

**JIT cut requirement 1 — Capture the pinned official checkpointer DDL**

Use a disposable PostgreSQL 18 database, set `search_path=kokoro,pg_catalog`, install `langgraph-checkpoint-postgres==3.1.0` and `psycopg[binary]==3.3.4`, and run `AsyncPostgresSaver.setup()`. Assert the resulting user-table set is exactly `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`; then dump with four explicit `--table=kokoro.<name>` arguments plus `--schema-only --no-owner --no-privileges`. Separately dump only `kokoro.checkpoint_migrations` with `--data-only --inserts --column-inserts --no-owner --no-privileges`, strip nondeterministic session comments/settings, and append those exact official version rows after the four table definitions. Normalize the combined DDL+seed into both the immutable vendor evidence file and the composed `45-langgraph-checkpointer.sql` segment. A fresh PG18 test compares every migration row and `max(v)` byte-for-byte with a separate database initialized by 3.1.0 `setup()`. Commit source package/version, setup/dump commands and SHA-256 headers. The composed segment must create and seed the tables in `kokoro`, and Agent startup must never call `setup()`.

**JIT cut requirement 2 — Write failing admission and routing tests**

Implement these tests against live PG18:

- `preparing` and `admission_failed` may have no manifest; `queued` without a same-run manifest fails at commit.
- Reusing `launch_id` with the same `launch_request_digest` resolves the existing run; changing the digest is rejected and preserves the first row.
- Duplicate `(agent_run_id, command_id)` control rows replay, while a digest change conflicts.
- `agent_run.next_event_seq` allocates a run-global cursor; `agent_event_outbox` rejects duplicate `(agent_run_id,seq)` even across different epochs, while stale-epoch emit is rejected.
- `agent_projection_ack(projected_epoch,projected_seq)` rejects old epoch and global-sequence regression. A recovery fixture writes epoch 1 seq 10, advances the lease, writes epoch 2 seq 11, and proves the cursor query after 10 yields only 11.
- An empty Capability snapshot header with no item table is valid; catalog lookup proves the item table is absent. Two concurrent inserts for the same `(organization_id,scope_key,digest)` yield one snapshot and one replay result; Slice A has no nullable Project column.
- A routing policy pointing at a draft Model revision fails at commit; the same published revision succeeds.
- A published revision with `transport=direct|local` cannot become a live routing target in Slice A; only `litellm` commits.
- A new provider is bootstrapped with the only Slice A health value `status=unknown`; catalog inspection proves no observation table or `last_observation_id` column was preinstalled.
- Every terminal Agent state rejects a later transition back to preparing/queued/running.

**JIT cut requirement 3 — Run RED**

```bash
uv run --isolated --project database --frozen pytest database/tests/test_agent_control_native_pg18.py -q
```

Expected: missing `agent_*`, `capability_*`, `model_*` and official checkpointer relations.

**JIT cut requirement 4 — Implement the remaining source segments and run GREEN**

Implement the exact Slice A columns and constraints from canonical data model §0.2. `agent_run` owns launch idempotency and the admission state machine; `agent_execution_manifest` is immutable and required before `queued`; `capability_runtime_snapshot` is the organization/namespace empty-header fact; Model current/routing pointers use same-model composite keys plus a deferred published-state trigger. Then run:

```bash
uv run --isolated --project database --frozen pytest database/tests/test_agent_control_native_pg18.py -q
git add database/schema/40-agent.sql database/schema/45-langgraph-checkpointer.sql \
  database/schema/50-capability.sql database/schema/60-model.sql \
  database/schema/99-cross-capability-relations.sql database/vendor \
  database/tests/test_agent_control_native_pg18.py
git commit -m "feat(database): add Agent control schema"
```

The `agent_execution_manifest` Slice A shape includes `usage_mode`, `usage_policy_digest` and no hold/price FK. The Model routing trigger rejects `model_revision.published_at IS NULL`. Capability snapshot contains only header identity and digest.

**JIT cut requirement 5 — Compose only from the clean committed segment set**

```bash
test -z "$(git status --short)"
uv run --project database --frozen python scripts/database/compose_baseline.py --write --require-clean
git add -f database/baseline/kokoro.sql database/baseline/manifest.json
git commit -m "build(database): compose Slice A baseline"
uv run --project database --frozen python scripts/database/compose_baseline.py --check --require-clean
uv run --isolated --project database --frozen pytest database/tests -q
```

**JIT cut requirement 6 — Add the isolated lane database runner**

`run_in_fresh_pg18_native.py` accepts `--label`, `--cwd`, optional `--baseline` (default
`database/baseline/kokoro.sql`) and a command after `--`. It locates `pg_config`, `initdb` and `pg_ctl`, rejects
anything other than PostgreSQL 18, creates a unique temporary parent and a not-yet-existing data-directory child,
initializes a local cluster and binds it to a dynamically reserved loopback port and private Unix-socket directory.
It creates database `kokoro` plus login/owner `kokoro_app`, applies the committed baseline once as `kokoro_app`,
then runs the child command with both `DATABASE_URL_KOKORO_APP` and `KOKORO_TEST_DATABASE_URL` set to that unique
URL. A signal-aware `finally` block stops the exact postmaster with `pg_ctl`, verifies its PID and sockets are gone,
and removes the temporary parent on command success, failure, SIGINT or SIGTERM. It never reuses
`127.0.0.1:5432`, and `--require-clean` rejects a dirty or uncommitted baseline.

`test_fresh_pg18_native_runner.py` starts two native clusters concurrently with labels `chat` and `agent`, writes
a marker table in each child command, proves neither database sees the other's marker, then forces one child command
to exit 7 and proves both postmasters, socket directories and temporary parents were removed. Run and commit:

```bash
uv run --isolated --project database --frozen pytest database/tests/test_fresh_pg18_native_runner.py -q
git add scripts/database/run_in_fresh_pg18_native.py database/tests/test_fresh_pg18_native_runner.py
git commit -m "test(database): isolate capability lane databases"
```

### Milestone 5: Generate owner inventory and owner-scoped Prisma schemas

**Files:**
- Create: `database/owner-inventory.json`
- Create: `database/writer-inventory.json`
- Create: `scripts/database/capture_catalog.py`
- Create: `scripts/database/render_owner_prisma.py`
- Create: `database/tests/test_owner_inventory.py`
- Create generated artifacts: `database/prisma/{iam,chat,capability,model}.prisma`; the IAM schema contains both `site_*` and `iam_*` tables.

**Interfaces:**
- Produces: `capture_catalog(conn) -> Catalog`, `render_owner_schema(catalog, owner) -> str`, and `install_owner_schema(owner, repo) -> Path`. The CLI reads exactly `DATABASE_URL_KOKORO_APP`; it never assumes localhost or starts an implicit shared server.

**JIT cut requirement 1 — Write a failing exact-coverage test**

The Root source test must apply the baseline and assert every manifest table appears exactly once in `owner-inventory.json`, every FK target exists, every owner prefix matches and no Slice B/C model is rendered. The explicit ownership map assigns both `site_*` and `iam_*` to `kokoro-iam`, and the runtime child allowlist is exactly IAM, Model, Capability, Chat, Agent and Web. It also asserts every one of the 50 owner tables has exactly one checked writer entry, singular gateway, authorized-command inventory and syntactically valid planned behavior-test path. It does not require child files that are created only in later lanes; the final promotion gate resolves and executes those paths against the six reviewed child commits.

Each `writer-inventory.json` row has this exact shape:

```json
{
  "table": "chat_run_launch",
  "ownerRepository": "kokoro-chat",
  "writerGateway": "ChatTransaction.runs",
  "authorizedCommands": ["SubmitMessage", "RecordAdmission"],
  "stateColumnsByCommand": {
    "SubmitMessage": ["launch_state", "created_at"],
    "RecordAdmission": ["launch_state", "accepted_agent_run_id", "updated_at"]
  },
  "lockOrClaim": "organization command receipt plus conversation active-run slot",
  "behaviorTestsByCommand": {
    "SubmitMessage": ["tests/application/submit-message.test.ts"],
    "RecordAdmission": ["tests/recovery/launch-outbox-worker.test.ts"]
  }
}
```

`writerGateway` is singular. Multiple command callers are listed separately rather than represented as multiple table writers. `behaviorTestsByCommand` has exactly the same keys as `authorizedCommands`, each value is a non-empty exact path list, and every authorized mutation path therefore has executable evidence. Root source tests validate exact 50-row coverage and schema; the final promotion gate resolves and executes every listed test against the promoted child commit.

**JIT cut requirement 2 — Implement catalog capture and rendering**

Render only scalar fields for cross-owner FKs; render same-owner relations only when they do not create a Prisma relation cycle. `install_owner_schema` copies the exact rendered bytes into the candidate repository and records the Root SQL/catalog digest in a sibling manifest. The IAM artifact is a single owner schema over both the Site FK roots and IAM tables. Every schema uses:

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL_KOKORO_APP")
}
```

No migration block or custom generator output is emitted. Each standalone repository has exactly one owner-scoped schema, so Prisma 6 generates its scoped client and native engine into standard `node_modules/@prisma/client`; the production image copies production `node_modules` and runs a real query smoke test from the final stage. The only datasource URL expression is the required `env("DATABASE_URL_KOKORO_APP")`; child runtime code may override it through Prisma's `datasourceUrl`, but no second variable or owner-specific URL exists.

**JIT cut requirement 3 — Validate generated schemas**

```bash
uv run --project database --frozen python scripts/database/run_in_fresh_pg18_native.py --label root-catalog --cwd "$PWD" -- \
  uv run --project database --frozen python scripts/database/capture_catalog.py --write
uv run --project database --frozen python scripts/database/render_owner_prisma.py --write
for owner in iam chat capability model; do
  uv run --project database --frozen python scripts/database/render_owner_prisma.py --install "$owner" "/tmp/kokoro-$owner-slice-a"
done
uv run --isolated --project database --frozen pytest database/tests/test_owner_inventory.py -q
for schema in database/prisma/*.prisma; do
  DATABASE_URL_KOKORO_APP=postgresql://kokoro_app:kokoro@127.0.0.1:1/kokoro \
    pnpm exec prisma validate --schema "$schema"
done
```

**JIT cut requirement 4 — Commit**

```bash
git add database/owner-inventory.json database/writer-inventory.json database/prisma scripts/database database/tests
git commit -m "build(database): generate owner Prisma schemas"
```

### Milestone 6: Consume the completed contract barrier without regeneration

The prerequisite `2026-08-14-slice-a-contract-manifest-barrier-roadmap.md` has already produced the reviewed machine manifest, nine Proto files, exact OpenAPI, first immutable Buf breaking image, consumer allowlist and deterministic generator in one clean Root contract-source commit. This SQL roadmap must not recreate, reformat, overwrite or delete any of those authority files. The master roadmap's structured retirement boundary is the only explanation of the frozen compatibility exception. This roadmap's contract gate is:

```bash
uv run --frozen python contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
uv run --frozen pytest contract/tests scripts/contract/tests -q
pnpm exec buf format --diff --exit-code contract/proto
pnpm exec buf lint contract
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
```

Expected: all pass against the existing barrier commit. Consumer generation for candidate repositories reads that exact contract-source commit; the later Root SQL commit cannot become a substitute provenance source.

### Milestone 7: Final Root source verification

**Files:** All files in this plan.

**JIT cut requirement 1 — Rebuild twice and compare bytes**

```bash
uv run --project database --frozen python scripts/database/compose_baseline.py --write
cp database/baseline/kokoro.sql /tmp/kokoro-a.sql
uv run --project database --frozen python scripts/database/compose_baseline.py --write
cmp /tmp/kokoro-a.sql database/baseline/kokoro.sql
```

**JIT cut requirement 2 — Run complete source gates**

```bash
uv run --isolated --project database --frozen pytest database/tests -q
uv run --frozen pytest contract/tests scripts/contract/tests -q
pnpm exec buf format --diff --exit-code contract/proto
pnpm exec buf lint contract
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
uv run --project database --frozen python scripts/database/compose_baseline.py --check
ROOT_CURRENT="$(git rev-parse --show-toplevel)"
ROOT_CONTRACT_COMMIT="$(git log -1 --format=%H -- contract)"
CONTRACT_WORKTREE_PARENT="$(mktemp -d /tmp/kokoro-contract-source.XXXXXX)"
CONTRACT_WORKTREE="$CONTRACT_WORKTREE_PARENT/root"
git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"
trap 'git worktree remove --force "$CONTRACT_WORKTREE" 2>/dev/null || true; rm -rf "$CONTRACT_WORKTREE_PARENT"' EXIT
(cd "$CONTRACT_WORKTREE" && pnpm install --frozen-lockfile && uv sync --frozen --group dev)
RUNTIME_CONSUMER_MAP=/tmp/kokoro-slice-a-runtime-consumer-map.json
cat >"$RUNTIME_CONSUMER_MAP" <<JSON
{"iam":"/tmp/kokoro-iam-slice-a","chat":"/tmp/kokoro-chat-slice-a","agent":"/tmp/kokoro-agent-slice-a","capability":"/tmp/kokoro-capability-slice-a","model":"/tmp/kokoro-model-slice-a","web":"/tmp/kokoro-web-slice-a","root-e2e":"$ROOT_CURRENT"}
JSON
# This is the fail-closed runtime allowlist. The frozen registry remains checked by the contract suite;
# the compatibility-only consumer documented in the master retirement boundary is deliberately absent here.
python3 - "$RUNTIME_CONSUMER_MAP" <<'PY'
from pathlib import Path
import json
import sys

RUNTIME_CONSUMERS = {"iam", "chat", "agent", "capability", "model", "web", "root-e2e"}
consumer_map = json.loads(Path(sys.argv[1]).read_text())
assert set(consumer_map) == RUNTIME_CONSUMERS, (set(consumer_map), RUNTIME_CONSUMERS)
assert "site" not in consumer_map
assert all(isinstance(path, str) and path for path in consumer_map.values())
PY
while IFS=$'\t' read -r consumer repo; do
  (cd "$CONTRACT_WORKTREE" && uv run --frozen python contract/generate.py \
    --source-root "$CONTRACT_WORKTREE" --source-commit "$ROOT_CONTRACT_COMMIT" \
    --consumer "$consumer" --repo "$repo" --check)
done < <(python3 - "$RUNTIME_CONSUMER_MAP" <<'PY'
from pathlib import Path
import json
import sys

consumer_map = json.loads(Path(sys.argv[1]).read_text())
for key in ("iam", "chat", "agent", "capability", "model", "web", "root-e2e"):
    consumer = key if key == "root-e2e" else f"kokoro-{key}"
    print(f"{consumer}\t{consumer_map[key]}")
PY
)
git worktree remove --force "$CONTRACT_WORKTREE"
rm -rf "$CONTRACT_WORKTREE_PARENT"
trap - EXIT
git diff --check
```

**JIT cut requirement 3 — Request independent review and freeze the Root source commit**

Review must cover exact 50+4 tables, tenant composite FKs, published Model routing, checkpointer version pin, no later-slice tables, deterministic outputs and exact service/method inventory.
