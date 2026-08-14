# Slice A Agent PostgreSQL and gRPC Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before a lane starts, its next milestone MUST be expanded into a separately reviewed JIT implementation cut with exact files, actual RED test/code, self-contained commands and one precise commit; workers never invent omitted code from this roadmap.

**Goal:** Move Agent durable state from MongoDB to the Root-owned PostgreSQL schema and expose the mature GA runtime through one gRPC-compatible service without rewriting execution, HITL, supervisor, tool-effect or LiteLLM behavior.

**Architecture:** Chat calls Agent through generated Protobuf/gRPC. `LaunchRun` performs only admission and durable run/outbox creation. An internal dispatcher publishes the committed request to the existing worker path. The supervisor, DeepAgent assembly, LangGraph execution, HITL and Redis live transport stay intact; their persistence ports are replaced by PostgreSQL adapters. Root installs the exact pinned LangGraph checkpointer tables, so Agent never runs DDL.

**Tech Stack:** Python 3.11+ with Pyright target 3.11, psycopg 3.3.4 async pool, SQLAlchemy-free repositories, grpcio, generated Protobuf, Redis Streams, LangGraph checkpoint-postgres 3.1.0, LiteLLM-compatible provider path, pytest, Ruff, Pyright.

## Global Constraints

- Work only in `/tmp/kokoro-agent-slice-a`, created from `kokoro-agent@18b394dc3df019244875e643c142c2b08b9db708`, plus the frozen Root contract commit. Do not edit the canonical Root submodule checkout.
- Preserve `RunScope(namespace, session_id, run_id, thread_id)` opacity. The admission boundary receives Site/organization IDs solely to resolve frozen references; it never forwards them, user IDs, roles or permissions into GA state/tools.
- Preserve supervisor lease/CAS, control inbox, claim-before-external-effect, durable event outbox, terminal fence, checkpoint/resume, HITL and usage aggregation semantics.
- Keep `src/kokoro_agent/model/factory.py` and its LiteLLM/OpenAI-compatible invocation path. Model RPC resolves catalog/routing only; it does not proxy token streams.
- Slice A uses an explicit empty Capability snapshot and unmetered execution. No Skill/MCP catalog writer, object store, Credit hold or pricing client is constructed.
- Agent startup verifies schema/version/checkpointer presence and fails closed; it never calls `CREATE`, `ALTER`, migration or `PostgresSaver.setup()`.
- PostgreSQL is durable truth. Redis remains a live queue/cache and can be rebuilt from committed dispatch/event outboxes.
- Agent gRPC and health share port 7206. Agent accepts only Chat's workload token and uses its own token for Model/Capability RPC; tokens are file-backed, constant-time checked and excluded from frozen GA payloads/logs.

---

### Milestone 1: Add generated RPC contracts and strict runtime configuration

**Files:**
- Generate atomically: `src/kokoro_agent/generated/**`, including common identity, Agent Runtime/events, Capability Runtime and Model Catalog `*_pb2.py`/`*_pb2_grpc.py` plus `provenance.json`
- Modify: `src/kokoro_agent/config.py`, `config_file.py`, `pyproject.toml`, `.env.example`
- Test: `tests/test_contract_gate.py`, `tests/test_config_file.py`, `tests/test_slice_a_runtime_config.py`

**JIT cut requirement 1 — Write RED tests**

- Remove each required Database/Redis/Capability/Model/gRPC-bind setting in turn and assert startup returns the exact missing-config error before opening a listener.
- Supply Mongo, direct provider secret and Hub registry production keys and assert Slice A parsing rejects them instead of silently ignoring them.
- Change one generated output byte and one source commit in a temporary manifest; assert the contract gate rejects both, then assert the untouched generated tree passes.

**JIT cut requirement 2 — Generate, do not hand-edit, Python consumers**

Use the Root consumer command recorded in generated provenance. Pin `grpcio==1.83.0`, `grpcio-health-checking==1.83.0`, the existing compatible `protobuf==6.33.6`, `langgraph-checkpoint-postgres==3.1.0` and `psycopg[pool]==3.3.4` through `uv.lock`; Slice A does not carry an unrelated Protobuf major upgrade.

**JIT cut requirement 3 — Define the exact configuration surface**

```python
@dataclass(frozen=True)
class SliceARuntimeConfig:
    database_url: str
    redis_url: str
    grpc_bind: str
    chat_workload_token_file: str
    agent_workload_token_file: str
    litellm_endpoint: str
    litellm_api_key_file: str
    capability_endpoint: str
    model_endpoint: str
    worker_id: str
    schema: str = "kokoro"
```

Production fixes `grpc_bind` to `0.0.0.0:7206` and `litellm_endpoint` to `http://litellm:4000`; tests may bind an ephemeral loopback port. The Chat token authenticates inbound RPC, the Agent token authenticates outbound Model/Capability clients, and the LiteLLM key authenticates the existing OpenAI-compatible client. Read and validate all files before opening the listener.

Remove production requirements for Mongo, Hub registry, MCP secret service, S3 package registry and direct provider credentials from Slice A startup. Keep those parsers only behind explicit later-slice feature flags and prove they are not instantiated.

**JIT cut requirement 4 — Verify and commit**

```bash
(cd /tmp/kokoro-agent-slice-a && \
  uv run pytest tests/test_contract_gate.py tests/test_config_file.py tests/test_slice_a_runtime_config.py -q && \
  uv run ruff check src tests && uv run pyright && \
  git add pyproject.toml uv.lock .env.example src/kokoro_agent/config.py src/kokoro_agent/config_file.py src/kokoro_agent/generated tests && \
  git commit -m "chore(agent): consume Slice A runtime contracts")
```

### Milestone 2: Implement the PostgreSQL unit of work and Agent repositories

**Files:**
- Create: `src/kokoro_agent/persistence/postgres/pool.py`, `unit_of_work.py`, `run_repository.py`, `lease_repository.py`, `control_repository.py`, `outbox_repository.py`, `effect_repository.py`, `usage_repository.py`, `memory_repository.py`, `sandbox_repository.py`, `dlq_repository.py`
- Create: `src/kokoro_agent/persistence/ports.py`
- Modify: `src/kokoro_agent/storage/ledger.py`, `storage/memory_store.py`
- Test: `tests/postgres/test_agent_unit_of_work.py`, `test_agent_repository_concurrency.py`, `test_agent_schema_negative.py`

**JIT cut requirement 1 — Port the existing ledger behavior tests before implementation**

The PG suite must execute these real cases:

- Claim one launch twice with one digest and once with drift; assert one run, exact replay and typed conflict.
- Barrier two supervisors on one lease; assert one owner, monotonic lease generation and loser rejection.
- Append duplicate/out-of-order controls; assert identity deduplication and committed consumption order.
- Drive a run to each terminal state and assert every attempted revival is rejected.
- Inject a failure between terminal state and event-outbox insert and assert both roll back; success commits both.
- Claim/finalize one tool effect, replay the same digest and conflict a changed digest without a second external invocation.
- Commit terminal usage lines and aggregate, then assert sum/digest equality and exact replay.
- Insert expired and live memory rows, run `ExpireMemory(now,batchSize)`, assert only expired rows are removed and a second run is an exact no-op.

**JIT cut requirement 2 — Run RED against a freshly applied Root baseline**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-repository-red --cwd /tmp/kokoro-agent-slice-a -- \
  uv run pytest tests/postgres -q)
```

**JIT cut requirement 3 — Implement one transaction boundary**

```python
@dataclass(frozen=True)
class AgentTransaction:
    runs: RunRepository
    leases: LeaseRepository
    controls: ControlRepository
    outboxes: OutboxRepository
    effects: ToolEffectRepository
    usage: UsageRepository
    memory: MemoryRepository
    sandboxes: SandboxRepository
    dlq: DispatchDlqRepository

    @classmethod
    def from_connection(cls, connection: AsyncConnection[dict[str, object]]) -> "AgentTransaction":
        return cls(
            runs=PostgresRunRepository(connection),
            leases=PostgresLeaseRepository(connection),
            controls=PostgresControlRepository(connection),
            outboxes=PostgresOutboxRepository(connection),
            effects=PostgresToolEffectRepository(connection),
            usage=PostgresUsageRepository(connection),
            memory=PostgresMemoryRepository(connection),
            sandboxes=PostgresSandboxRepository(connection),
            dlq=PostgresDispatchDlqRepository(connection),
        )

class PostgresAgentUnitOfWork:
    def __init__(self, pool: AsyncConnectionPool[AsyncConnection[dict[str, object]]]) -> None:
        self._pool = pool

    @asynccontextmanager
    async def transaction(
        self, isolation: IsolationLevel = IsolationLevel.SERIALIZABLE
    ) -> AsyncIterator[AgentTransaction]:
        async with self._pool.connection() as connection:
            async with connection.transaction():
                await connection.execute(isolation.set_transaction_sql)
                yield AgentTransaction.from_connection(connection)
```

`IsolationLevel.set_transaction_sql` is an enum-owned two-value static SQL object (`SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` or `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ`), executed before the first repository statement; no caller text is interpolated. Tests observe the effective isolation with `SHOW transaction_isolation` for both values and prove the pool returns to its default after exit. Every repository accepts the transaction connection explicitly. Advisory locks, `FOR UPDATE`, compare-and-set state and outbox allocation are registered SQL constants, not dynamic query fragments.

**JIT cut requirement 4 — Implement exact multi-writer row ownership**

- Admission owns `preparing` row creation and immutable manifest binding.
- Admission owns `preparing -> queued|admission_failed`; Supervisor owns `queued -> running <-> awaiting_input -> completed|cancelled|failed` under lease/generation fences.
- Control receiver only appends inbox commands; supervisor consumes them.
- Event publisher only marks committed outbox delivery metadata.
- Usage writer appends run-owned lines and final aggregate in the same terminal transaction.

**JIT cut requirement 5 — Verify and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-repository-green --cwd /tmp/kokoro-agent-slice-a -- \
  uv run pytest tests/postgres -q)
cd /tmp/kokoro-agent-slice-a
uv run ruff check src tests && uv run pyright
git -C /tmp/kokoro-agent-slice-a add src/kokoro_agent/persistence src/kokoro_agent/storage/ledger.py src/kokoro_agent/storage/memory_store.py tests/postgres
git -C /tmp/kokoro-agent-slice-a commit -m "feat(agent): persist runtime state in PostgreSQL"
```

### Milestone 3: Bind the pinned LangGraph PostgreSQL checkpointer

**Files:**
- Modify: `src/kokoro_agent/storage/checkpoints.py`
- Create: `src/kokoro_agent/persistence/postgres/checkpointer.py`
- Test: `tests/postgres/test_checkpointer_compatibility.py`, `tests/test_invoke.py`, `tests/test_swarm.py`

**JIT cut requirement 1 — Write RED compatibility tests**

- Drop each official checkpoint table in a disposable database and assert startup fails before worker readiness.
- Change the latest `checkpoint_migrations` version and assert exact incompatibility failure.
- Pause a real graph, close the process/pool, start a new process and assert resume from the same thread/checkpoint reaches one terminal result.
- Wrap the connection with a statement recorder and assert startup/execution emits no `CREATE`, `ALTER`, `DROP` or setup call.

**JIT cut requirement 2 — Construct the official saver without setup**

Set `search_path=kokoro,pg_catalog`, verify the pinned `checkpoint_migrations` version, then construct the official async saver with a dedicated pool using the same `database_url`, `autocommit=True`, `prepare_threshold=0` and `dict_row` row factory required by the official implementation. This is a connection-lifecycle separation, not another database role or authority. Do not fork its SQL, change table shapes or call setup.

**JIT cut requirement 3 — Run existing checkpoint/HITL suites plus PG restart test**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-checkpointer --cwd /tmp/kokoro-agent-slice-a -- \
  uv run pytest tests/postgres/test_checkpointer_compatibility.py tests/test_invoke.py tests/test_swarm.py tests/test_hitl.py -q)
git -C /tmp/kokoro-agent-slice-a add src/kokoro_agent/storage/checkpoints.py src/kokoro_agent/persistence/postgres/checkpointer.py tests/postgres/test_checkpointer_compatibility.py
git -C /tmp/kokoro-agent-slice-a commit -m "feat(agent): use Root-installed LangGraph checkpoints"
```

### Milestone 4: Implement admission and the Agent gRPC service

**Files:**
- Create: `src/kokoro_agent/application/admission.py`, `runtime_service.py`, `capability_client.py`, `model_client.py`, `proto_mapping.py`
- Create: `src/kokoro_agent/interfaces/grpc/server.py`, `agent_runtime_service.py`, `interceptors.py`
- Test: `tests/test_agent_runtime_service.py`, `tests/test_agent_admission.py`, `tests/test_agent_grpc_integration.py`

**JIT cut requirement 1 — Write RED service tests**

- Assert transaction A commits `preparing` before fake Capability/Model clients are called, no DB transaction remains open during those RPCs, and transaction B commits manifest/queued/outbox together.
- Return a deterministic dependency rejection and assert `admission_failed`, no manifest and no dispatch; return timeout and assert retryable `preparing`.
- Send a syntactically valid unknown Agent preset/model label and a nonempty Capability selector list; assert deterministic admission rejection in all three cases and prove Chat later releases its active slot through the frozen failure convergence.
- Replay the same launch/digest and assert the same run; drift returns `ALREADY_EXISTS` and preserves the original.
- Send control, crash after DB commit but before response, retry and assert one durable control plus the same receipt.
- Ack sequence `10`, then `9`, and assert stored ack remains `10`.
- Call every method with Chat, wrong and absent workload identities; only exact Chat identity succeeds.
- Capture the GA invocation input and assert Site/organization/principal/RBAC fields are absent after admission finalizes.
- Send only `requested_agent_preset_key`; resolve its code-owned definition inside Agent, then resolve `ModelSelection(transport=litellm, providerModelName=slice-a-fixture)` plus the empty Capability snapshot. Finalize and dispatch; assert the manifest freezes the resolved preset digest and the mature request preserves original `message_id/content`, `context(namespace,session_id)`, `thread_id=session_id`, `ModelConfig(provider=litellm,name=slice-a-fixture)`, preset tools/permissions and empty Skill/MCP lists. A caller-supplied preset digest field is absent/rejected.

**JIT cut requirement 2 — Implement the reviewed two-transaction admission**

1. `ClaimLaunch` opens serializable transaction A, claims `launch_id + launch_request_digest` and inserts or rereads `agent_run(preparing)`; same digest returns the existing run, drift returns conflict, then the transaction commits.
2. With no database transaction open, resolve the organization/namespace Capability snapshot and Site Model revision using the request's admission-only tuple. Capability command identity is deterministic: `UUIDv5(launch_id, "capability-snapshot-v1")`; its request digest covers organization ID, opaque namespace and requested capability selectors. Timeout/retry reuses that exact identity. Validate the Capability response's echoed organization/scope and both canonical digests; Model selection is bound to the requested Site by Model's own routing-policy FK and does not invent a nonexistent Site echo field.
3. `FinalizeAdmission` opens serializable transaction B, locks the preparing run, inserts the immutable manifest (including original input `message_id/content`, frozen `session_id`, `thread_id=session_id`, the Agent-resolved code-owned preset key/digest, selectors, resolved references, `usage_mode="unmetered"` and `usage_policy_digest=sha256("kokoro.usage.unmetered.v1")`), CASes `preparing -> queued` and inserts dispatch outbox, then commits.
4. A deterministic dependency rejection opens a short transaction, CASes `preparing -> admission_failed` and creates no manifest/outbox. A timeout/unknown outcome leaves `preparing` for exact retry/reconciliation and never invents another run.
5. Dispatch reconstructs the mature strict `RunRequest` with original `RunInput`, `(namespace, session_id, generated run_id, thread_id)`, code-owned AgentPreset tools/backend/permissions, `ModelConfig(provider="litellm",name=selection.provider_model_name)` and empty Capability Skill/MCP lists. It reads LiteLLM base URL/key only from process config. Slice A rejects `thread_id != session_id`; tenant-resolution axes are absent from GA state, checkpoint, tools and trace.

**JIT cut requirement 3 — Expose the exact service**

```python
class AgentRuntimeGrpcService(AgentRuntimeServiceServicer):
    def __init__(self, application: AgentRuntimeApplication) -> None:
        self._application = application

    async def LaunchRun(self, request: LaunchRunRequest, context: ServicerContext) -> LaunchRunResponse:
        return launch_run_response_to_proto(
            await self._application.launch_run(launch_run_request_from_proto(request))
        )

    async def ApplyControl(self, request: ApplyControlRequest, context: ServicerContext) -> ApplyControlResponse:
        return apply_control_response_to_proto(
            await self._application.apply_control(apply_control_request_from_proto(request))
        )

    async def ReadRunEvidence(self, request: ReadRunEvidenceRequest, context: ServicerContext) -> ReadRunEvidenceResponse:
        return read_run_evidence_response_to_proto(
            await self._application.read_run_evidence(read_run_evidence_request_from_proto(request))
        )

    async def AckProjection(self, request: AckProjectionRequest, context: ServicerContext) -> AckProjectionResponse:
        return ack_projection_response_to_proto(
            await self._application.ack_projection(ack_projection_request_from_proto(request))
        )
```

Validate Chat workload identity in an interceptor. The service does not expose Mongo IDs, Redis stream keys, provider credentials or LangGraph checkpoint internals.

**JIT cut requirement 4 — Verify and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-admission --cwd /tmp/kokoro-agent-slice-a -- \
  uv run pytest tests/test_agent_runtime_service.py tests/test_agent_admission.py tests/test_agent_grpc_integration.py -q)
git -C /tmp/kokoro-agent-slice-a add src/kokoro_agent/application src/kokoro_agent/interfaces tests/test_agent_runtime_service.py tests/test_agent_admission.py tests/test_agent_grpc_integration.py
git -C /tmp/kokoro-agent-slice-a commit -m "feat(agent): expose durable Agent runtime RPC"
```

### Milestone 5: Rebind the supervisor and event pipeline without rewriting GA

**Files:**
- Modify: `src/kokoro_agent/worker/supervisor.py`, `worker/main.py`, `execution/events.py`, `execution/publish_agent_events.py`, `execution/run_agent.py`, `execution/protocols.py`
- Create: `src/kokoro_agent/worker/dispatch_outbox.py`, `event_outbox.py`, `memory_retention.py`
- Test: `tests/test_supervisor.py`, `test_memory_retention.py`, `test_control_inbox.py`, `test_r0_fault_matrix.py`, `test_steering.py`, `test_request_human.py`, `tests/postgres/test_agent_restart_replay.py`

**JIT cut requirement 1 — Keep existing behavioral suites unchanged and add PG fault tests**

- Commit dispatch outbox, kill before Redis publish, restart and assert one worker claim/run.
- Commit an event, drop Redis publish/Chat ack, restart publisher and assert republish until monotonic ack without duplicate durable event.
- Kill after external tool effect but before finalize, run reconciler and assert it records the provider result without executing again.
- Inject failure at terminal event/usage/run boundaries and assert all roll back; success commits one terminal event plus exact aggregate.

**JIT cut requirement 2 — Adapt only persistence seams**

- Dispatch publisher reads `agent_dispatch_outbox` and publishes the existing worker message.
- Supervisor lease/control APIs use PG repositories with the same state machine.
- `RunEmitter` writes PG event outbox before Redis publish.
- Projection acknowledgement advances `agent_projection_ack`; retention only deletes acknowledged rows below the safe watermark. Slice A authenticates Chat and derives the only allowed consumer key `chat`; the request field must equal it. Empty/unknown keys return `INVALID_ARGUMENT` before any ack row access, cannot create unbounded consumers and cannot pin retention. Agent event `seq` is allocated under the run row and remains globally monotonic across lease epochs; epoch is a fence only. Tests force epoch 1 through seq 10, recover under epoch 2 and require seq 11, prove `ReadRunEvidence(after_seq=10)` returns exactly 11, and prove stale-epoch emit/ack plus sequence regression cannot advance state.
- Tool middleware uses claim → external effect → finalize/reconcile, never a transaction around the network call.
- `MemoryRetentionWorker` invokes `ExpireMemory(now,batch_size)` in bounded transactions, never deletes a live row, participates in stop/drain, and is the only production caller allowed to hard-delete expired `agent_memory`.

**JIT cut requirement 3 — Prove core GA preservation**

Run assembly, HITL, steering, tool policy, effect journal, checkpoint, subagent and LiteLLM tests. No test should require a production Mongo URI.

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-supervisor --cwd /tmp/kokoro-agent-slice-a -- \
  uv run pytest \
    tests/test_assembly.py tests/test_invoke.py tests/test_hitl.py tests/test_steering.py \
    tests/test_tool_journal_middleware.py tests/test_tool_policy_middleware.py \
    tests/test_supervisor.py tests/test_control_inbox.py tests/test_r0_fault_matrix.py \
    tests/test_litellm_gateway.py tests/postgres/test_agent_restart_replay.py -q)
git -C /tmp/kokoro-agent-slice-a add src/kokoro_agent/worker src/kokoro_agent/execution tests
git -C /tmp/kokoro-agent-slice-a commit -m "refactor(agent): bind supervisor to durable outboxes"
```

### Milestone 6: Hard-cut Slice A production composition from Mongo/Hub ownership

**Files:**
- Delete: `src/kokoro_agent/storage/mongo.py`
- Modify: `src/kokoro_agent/worker/main.py`, `src/kokoro_agent/skills/hub.py`, `src/kokoro_agent/mcp/registry.py`, `README.md`, `src/kokoro_agent/worker/INDEX.md`, `src/kokoro_agent/execution/INDEX.md`
- Modify baseline-gate files as needed without suppressions: `tests/test_assets.py`, `tests/test_skill_hub.py`, `tests/test_workspace_archive.py`, `tests/test_docker_backend.py`, `pyproject.toml`, `uv.lock`
- Test: `tests/test_architecture.py`, `tests/test_slice_a_composition.py`

**JIT cut requirement 1 — Add zero-call architecture tests**

- Import/construct Slice A production main with Mongo modules monkeypatched to fail and assert readiness still succeeds with zero calls.
- Monkeypatch Skill/MCP catalog writer, package and secret constructors to fail; empty snapshot execution must not call them.
- Resolve a model through the Model client and assert `model/factory.py` creates the existing LiteLLM path, not direct/local production transport.
- Instrument lifecycle factories and assert one gRPC server, one supervisor and one orderly close of each.
- Capture the pinned HEAD Ruff/Pyright RED before cleanup. Remove obsolete unused `SKIP_REASON` variables and module-order violations in the four named tests; refresh the lock/type dependencies required by the retained runtime. Pyright remains strict for `src` and `tests`; do not add blanket ignores, `Any` boundaries or exclude migrated files merely to turn the gate green.

**JIT cut requirement 2 — Remove production Mongo wiring**

Delete the Mongo ledger/checkpoint/memory composition. Keep Skill/MCP materialization code dormant for Slice B, but remove its production catalog mutation and official seeding authority. Empty snapshot resolution returns zero items and constructs no package/MCP clients.

**JIT cut requirement 3 — Run the complete Agent gate**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd /tmp/kokoro-agent-slice-a && uv sync --frozen)
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-full --cwd /tmp/kokoro-agent-slice-a -- uv run pytest -q)
(cd /tmp/kokoro-agent-slice-a && \
  uv run ruff check . && uv run pyright && uv lock --check --no-config && \
  { git grep -nE 'MONGO_URI|MongoClient|SkillHub\(' -- src/kokoro_agent/worker src/kokoro_agent/config.py && exit 1 || true; } && \
  git diff --check && \
  git add src tests README.md pyproject.toml uv.lock .env.example && \
  git commit -m "refactor(agent): hard cut Slice A runtime to PostgreSQL")
```

### Milestone 7: Prove restart, replay and gRPC compatibility on real infrastructure

**Files:**
- Create: `tests/e2e/test_slice_a_agent_runtime.py`, `tests/e2e/compose.agent.yml`
- Create: `tests/e2e/fake_dependencies.py`, `tests/e2e/openai_fixture.py`, `tests/e2e/create_fixture_secrets.py`
- Create: `deployables.yaml`
- Modify: `Dockerfile`

**Interfaces:**
- Consumes the committed Root `database/baseline/kokoro.sql` whose commit is recorded in generated provenance.
- Produces a standalone Agent candidate gate; it does not depend on uncommitted Root backend composition or real owner candidates.

**JIT cut requirement 1 — Write the failing real-infrastructure test**

The test uses generated clients only. It launches one run with `message_id/content`, `session_id=thread_id`, Site/organization admission axes and one opaque namespace; fake Capability returns the canonical organization-scope empty snapshot, fake Model returns `slice-a-fixture`, and real LiteLLM forwards to the deterministic OpenAI fixture. Assert one HITL request, durable SQL evidence, exact control replay, terminal output and usage totals.

**JIT cut requirement 2 — Add the self-contained test composition**

`tests/e2e/compose.agent.yml` contains exact services `postgres:18`, `database-init`, `redis:7`, `openai-fixture`, pinned LiteLLM image, `fake-dependencies`, and the local Agent image. `database-init` mounts the committed Root baseline read-only and applies it once; Agent never installs DDL. `fake-dependencies.py` hosts the generated Capability and Model gRPC services on separate ports, validates the Agent workload token and returns only the frozen values above. `create_fixture_secrets.py` writes fresh Chat/Agent/LiteLLM tokens mode 0600 under one marked temporary directory.

**JIT cut requirement 3 — Execute crash/restart and absence assertions**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
AGENT_ROOT=/tmp/kokoro-agent-slice-a
ROOT_CONTRACT_COMMIT="$(python3 -c 'import json; print(json.load(open("/tmp/kokoro-agent-slice-a/src/kokoro_agent/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git -C "$ROOT_SOURCE" log -1 --format=%H -- contract)"
export KOKORO_ROOT_SOURCE="$ROOT_SOURCE"
export KOKORO_AGENT_FIXTURE_SECRET_DIR="$(mktemp -d /tmp/kokoro-agent-e2e-secrets.XXXXXX)"
cleanup_agent_e2e() {
  (cd "$AGENT_ROOT" && docker compose -f tests/e2e/compose.agent.yml down -v --remove-orphans) || true
  rm -rf -- "$KOKORO_AGENT_FIXTURE_SECRET_DIR"
}
trap cleanup_agent_e2e EXIT
(cd "$AGENT_ROOT" && uv run python tests/e2e/create_fixture_secrets.py --dir "$KOKORO_AGENT_FIXTURE_SECRET_DIR")
(cd "$AGENT_ROOT" && docker compose -f tests/e2e/compose.agent.yml up -d --build)
(cd "$AGENT_ROOT" && uv run pytest tests/e2e/test_slice_a_agent_runtime.py -q)
(cd "$AGENT_ROOT" && docker compose -f tests/e2e/compose.agent.yml stop agent)
(cd "$AGENT_ROOT" && docker compose -f tests/e2e/compose.agent.yml start agent)
(cd "$AGENT_ROOT" && uv run pytest tests/e2e/test_slice_a_agent_runtime.py -q --restart-readback)
(cd "$AGENT_ROOT" && docker compose -f tests/e2e/compose.agent.yml exec -T agent sh -ec '! env | grep -E "MONGO|S3|HUB|DIRECT_PROVIDER"')
cleanup_agent_e2e
trap - EXIT
```

**JIT cut requirement 4 — Commit evidence-facing runtime material**

```bash
(cd /tmp/kokoro-agent-slice-a && uv run ruff check src tests && uv run pyright)
(cd /tmp/kokoro-agent-slice-a && docker build -t kokoro-agent:slice-a .)
git -C /tmp/kokoro-agent-slice-a add tests/e2e Dockerfile deployables.yaml
git -C /tmp/kokoro-agent-slice-a commit -m "test(agent): prove PostgreSQL restart and replay"
```

## Completion Criteria

- Agent has one gRPC-compatible service and one supervisor composition.
- All durable Agent-owned writes go through PostgreSQL owner repositories.
- The official pinned LangGraph checkpointer survives restart and Agent runs no DDL.
- Existing GA assembly/HITL/tool/supervisor semantics remain green.
- Mongo/Hub/Skill/MCP writers are absent from Slice A production composition.
- Real PG18 + Redis launch, HITL, crash, replay and terminal convergence pass.
