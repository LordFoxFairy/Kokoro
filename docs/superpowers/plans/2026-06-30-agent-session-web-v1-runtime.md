# Agent / Session / Web V1 Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Bring `kokoro-agent`, `kokoro-session`, and `kokoro-web` to the
approved V1 runtime design: Mongo-backed session truth, standard
snapshot + EventSource replay, and DeepAgents-native agent execution.

**Architecture:** `kokoro-session` owns chat state and browser-facing events;
`kokoro-agent` owns DeepAgents/LangChain execution and raw events;
`kokoro-web` owns UI projection only. Redis is queue/live/lease transport, not
history. Mongo is session truth. Web never sorts by `seq/cursor`.

**Tech Stack:** Bun + TypeScript (`kokoro-session`, `kokoro-web`), Python + uv
(`kokoro-agent`), MongoDB, Redis Streams, Next.js, DeepAgents/LangChain/
LangGraph.

---

## References

- `docs/kokoro-handbook/technical/11-agent-session-web-v1-runtime.md`
- `docs/kokoro-handbook/business-flows/agent-session-web-general-chat-runtime.md`
- `docs/kokoro-handbook/modules/kokoro-agent.md`
- `docs/kokoro-handbook/modules/kokoro-session.md`
- `docs/kokoro-handbook/modules/kokoro-web.md`
- `docs/kokoro-handbook/technical/03-agent-architecture.md`
- `docs/kokoro-handbook/technical/04-session-architecture.md`
- `docs/kokoro-handbook/technical/05-web-architecture.md`

## Current Preconditions

- `kokoro-session` SQLite runtime has already been removed.
- `makeMessageStore()` defaults to Mongo and rejects `sqlite`.
- `kokoro-session` tests/typecheck/lint already passed after SQLite removal.
- Handbook V1 runtime docs have been written and linted.
- Existing dirty subrepo state must be preserved; do not revert user or prior
  edits.

## Scope Guard

Only edit:

- `kokoro-agent/**`
- `kokoro-session/**`
- `kokoro-web/**`
- three-repo runtime docs under `docs/kokoro-handbook/**`
- this plan and follow-up test reports
- `docs/kokoro-handbook/operations/testing-checklist.md` for drift commands

Do not edit platform/payment/model/credit/site/user implementation except when
reading docs for context.
Do not add new root-level scripts for this task.

## Target File Structure

### kokoro-session

Create or reshape around:

```text
src/domain/session.ts
src/domain/message.ts
src/domain/run.ts
src/domain/session-event-log.ts
src/domain/agent-run-input.ts
src/application/session-service.ts
src/application/session-replay.ts
src/application/relay-run.ts
src/application/start-run.ts
src/infrastructure/session-store/mongo.ts
src/infrastructure/session-store/memory.ts
src/interfaces/http.ts
src/interfaces/sse-endpoint.ts
tests/session-store.test.ts
tests/session-api.test.ts
tests/session-replay.test.ts
tests/relay-run.test.ts
```

Keep `message-store` only as a temporary compatibility name while migrating;
final code should call the production abstraction `SessionStore` or
`SessionRepository`.

### kokoro-web

Create or reshape around:

```text
src/application/session/transport.ts
src/application/session/reducer.ts
src/application/session/snapshot.ts
src/application/session/types.ts
src/application/session/transport-schema.ts
src/interfaces/chat/*
tests/session-transport.test.ts
tests/session-reducer.test.ts
tests/session-snapshot.test.ts
```

Remove product use of `seq`, `cursor`, `lastResumeId`, and `?after=`.

### kokoro-agent

Create or reshape around:

```text
src/kokoro_agent/domain/agent_run_input.py
src/kokoro_agent/domain/backend_policy.py
src/kokoro_agent/domain/raw_event.py
src/kokoro_agent/application/run_supervisor.py
src/kokoro_agent/application/approval_flow.py
src/kokoro_agent/application/event_projection.py
src/kokoro_agent/infrastructure/deepagents_runtime.py
src/kokoro_agent/infrastructure/backend_config.py
src/kokoro_agent/infrastructure/tools/web_fetch.py
src/kokoro_agent/infrastructure/tools/now.py
src/kokoro_agent/interfaces/worker.py
tests/test_agent_run_input.py
tests/test_deepagents_runtime.py
tests/test_approval_flow.py
tests/test_raw_events.py
```

Avoid business logic in `__init__.py`. Avoid `Factory/Manager/Coordinator`
style names unless they remove real complexity.

---

## Chunk 1: Session Data Model And API

### Task 1.1: Lock Session Store Contract

**Files:**

- Create: `kokoro-session/tests/session-store.test.ts`
- Create: `kokoro-session/src/domain/session.ts`
- Create: `kokoro-session/src/domain/message.ts`
- Create: `kokoro-session/src/domain/run.ts`
- Create: `kokoro-session/src/domain/session-event-log.ts`
- Create: `kokoro-session/src/application/session-store.ts`

- [ ] **Step 1: Write failing domain/store tests**

Test these behaviors:

```ts
test("creates a user message, assistant placeholder, run, and activeRunId atomically")
test("same idempotencyKey returns the original messageId and runId")
test("different idempotencyKey is rejected while a run is active")
test("terminal event clears activeRunId in the same commit")
test("duplicate eventId is stored once")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-session
bun test tests/session-store.test.ts
```

Expected: tests fail because `SessionStore` and models do not exist.

- [ ] **Step 3: Implement minimal domain types**

Add focused TypeScript types:

```ts
export type ChatSession = {
  siteId: string
  sessionId: string
  ownerUserId: string
  activeRunId: string | null
  status: "active" | "archived" | "deleted"
  createdAt: Date
  updatedAt: Date
}

export type AgentRunStatus =
  | "queued"
  | "running"
  | "awaiting_approval"
  | "completed"
  | "failed"
  | "cancelled"
  | "timeout"
  | "enqueue_failed"
```

- [ ] **Step 4: Implement memory SessionStore**

Use memory fake only for unit tests. Do not add SQLite.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd kokoro-session
bun test tests/session-store.test.ts
bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git -C kokoro-session add src tests
git -C kokoro-session commit -m "feat: add session store contract"
```

### Task 1.2: Mongo Session Store

**Files:**

- Create: `kokoro-session/src/infrastructure/session-store/mongo.ts`
- Modify: `kokoro-session/src/infrastructure/message-store/factory.ts`
- Create: `kokoro-session/tests/session-store-mongo.test.ts`

- [ ] **Step 1: Write failing Mongo integration tests**

Cover:

```ts
test("persists sessions/messages/runs/events across clients")
test("active run admission is atomic under concurrent requests")
test("eventId unique index deduplicates relay retry")
test("terminal event clears activeRunId atomically")
```

Skip cleanly when `KOKORO_TEST_MONGO_URL` is unavailable.

- [ ] **Step 2: Run tests and verify RED/SKIP**

Run:

```bash
cd kokoro-session
bun test tests/session-store-mongo.test.ts
```

Expected: fail if Mongo is running and implementation is absent; skip if Mongo
is unavailable.

- [ ] **Step 3: Implement Mongo collections**

Collections:

```text
kokoro_session.sessions
kokoro_session.messages
kokoro_session.runs
kokoro_session.session_events
kokoro_session.outbox
```

Indexes:

```text
sessions: unique(siteId, sessionId)
messages: unique(siteId, sessionId, messageId)
runs: unique(siteId, runId), index(siteId, sessionId, status)
session_events: unique(siteId, sessionId, eventId), index(siteId, sessionId, sseId)
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd kokoro-session
bun test tests/session-store.test.ts tests/session-store-mongo.test.ts
bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git -C kokoro-session add src tests
git -C kokoro-session commit -m "feat: persist sessions in mongo"
```

### Task 1.3: Message-First HTTP API

**Files:**

- Modify: `kokoro-session/src/interfaces/http.ts`
- Create: `kokoro-session/src/domain/agent-run-input.ts`
- Modify: `kokoro-session/src/application/start-run.ts`
- Create: `kokoro-session/tests/session-api.test.ts`

- [ ] **Step 1: Write failing API tests**

Cover:

```ts
test("POST /sessions/:id/messages creates a run")
test("POST /sessions/:id/messages returns same run for same idempotencyKey")
test("POST /sessions/:id/messages rejects second active run")
test("GET /sessions/:id returns snapshot with eventWatermark")
test("old POST /sessions/:id/runs route is removed")
```

- [ ] **Step 2: Run API tests and verify RED**

Run:

```bash
cd kokoro-session
bun test tests/session-api.test.ts
```

- [ ] **Step 3: Implement request schemas**

Use strict Zod schemas. Request body includes:

```ts
idempotencyKey: string
content: string
attachments?: AttachmentRef[]
executionStyle?: "fast" | "thinking"
permissionMode?: "auto" | "default" | "plan"
selectedSkillIds?: string[]
selectedMcpServerIds?: string[]
selectedToolNames?: string[]
```

- [ ] **Step 4: Build AgentRunInput**

For V1, build a minimal but explicit object:

```ts
{
  siteId,
  workspaceId,
  projectId,
  sessionId,
  runId,
  userId,
  inputMessageId,
  assistantMessageId,
  context: {
    recentMessages,
    summary,
    artifactRefs,
    toolResultRefs,
    userProvidedFiles,
  },
  modelRuntime,
  executionStyle,
  permissionMode,
  backendPolicy,
  enabledSkills,
  enabledMcpServers,
  enabledTools,
  traceContext,
}
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd kokoro-session
bun test tests/session-api.test.ts tests/start-run.test.ts tests/http.test.ts
bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git -C kokoro-session add src tests
git -C kokoro-session commit -m "feat: add message-first session api"
```

---

## Chunk 2: Session Replay And Relay Durability

### Task 2.1: DB-First Relay

**Files:**

- Modify: `kokoro-session/src/application/relay-run.ts`
- Modify: `kokoro-session/src/application/normalize.ts`
- Create: `kokoro-session/tests/relay-run.test.ts`

- [ ] **Step 1: Write failing relay tests**

Cover:

```ts
test("stores event before publishing live")
test("terminal event updates run and clears activeRunId before live publish")
test("duplicate raw event does not duplicate session_event")
test("malformed raw event is skipped without poisoning mongo")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-session
bun test tests/relay-run.test.ts
```

- [ ] **Step 3: Implement DB-first order**

Order must be:

```text
strict parse raw event
normalize to SessionEvent
write session_events
update messages/runs projection
if terminal: set activeRunId=null in same DB operation scope
publish live / outbox
```

- [ ] **Step 4: Remove ordering dependence on Redis cursor**

Stop deriving `seq` from Redis cursor. Keep eventId stable by deterministic raw
identity:

```text
runId + raw event stable id + event kind + segment/tool/subagent id
```

If producer lacks stable raw id, session must derive one from run stream id only
as idempotency input, not as sort order.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd kokoro-session
bun test tests/relay-run.test.ts tests/normalize.test.ts
bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git -C kokoro-session add src tests
git -C kokoro-session commit -m "fix: persist session events before live publish"
```

### Task 2.2: Snapshot + EventSource Replay

**Files:**

- Modify: `kokoro-session/src/interfaces/sse-endpoint.ts`
- Modify: `kokoro-session/src/infrastructure/sse.ts`
- Create: `kokoro-session/src/application/session-replay.ts`
- Create: `kokoro-session/tests/session-replay.test.ts`

- [ ] **Step 1: Write failing replay tests**

Cover:

```ts
test("snapshot includes eventWatermark")
test("SSE replay starts after Last-Event-ID when present")
test("SSE replay starts after eventWatermark for snapshot attach")
test("Mongo replay to Redis live tail does not drop gap events")
test("unknown Last-Event-ID falls back to recoverable replay")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-session
bun test tests/session-replay.test.ts
```

- [ ] **Step 3: Implement handoff algorithm**

Implementation sequence:

```text
capture current Redis live tail id
read Mongo events after Last-Event-ID or snapshot eventWatermark
send replay events
tail Redis live from captured tail id
dedupe by eventId
send heartbeat comments and retry interval
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd kokoro-session
bun test tests/session-replay.test.ts tests/http.test.ts
bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git -C kokoro-session add src tests
git -C kokoro-session commit -m "feat: add snapshot-aware sse replay"
```

---

## Chunk 3: Web Snapshot Transport And Reducer

### Task 3.1: Transport API Alignment

**Files:**

- Modify or create: `kokoro-web/src/application/session/transport.ts`
- Modify or create: `kokoro-web/src/application/session/transport-schema.ts`
- Create: `kokoro-web/tests/session-transport.test.ts`

- [ ] **Step 1: Write failing transport tests**

Cover:

```ts
test("sendMessage posts JSON body to /sessions/:id/messages")
test("loadSnapshot calls GET /sessions/:id")
test("openEvents uses EventSource GET /sessions/:id/events")
test("openEvents may attach with snapshot eventWatermark")
test("transport never adds ?after or lastResumeId")
test("transport does not expose sseId as domain state")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-web
bun test tests/session-transport.test.ts
```

- [ ] **Step 3: Implement SessionTransport**

Expose:

```ts
sendMessage(sessionId, body): Promise<MessageRunResult>
loadSnapshot(sessionId): Promise<SessionSnapshot>
openEvents(sessionId, options, handlers): EventSourceHandle
sendControl(sessionId, runId, body): Promise<void>
```

`options.eventWatermark` is an attach hint from the latest snapshot. Transport
may pass it as `Last-Event-ID` or another server-owned internal header if the
runtime uses an EventSource polyfill. It must not become Web domain state and
must not be exposed as `lastResumeId`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd kokoro-web
bun test tests/session-transport.test.ts
bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git -C kokoro-web add src tests
git -C kokoro-web commit -m "feat: align web session transport"
```

### Task 3.2: Reducer Without seq/cursor

**Files:**

- Modify: `kokoro-web/src/application/session-stream/reducer.ts`
- Modify: `kokoro-web/src/application/session-stream/types.ts`
- Modify: `kokoro-web/src/application/session-stream/state-schema.ts`
- Create: `kokoro-web/tests/session-reducer.test.ts`

- [ ] **Step 1: Write failing reducer tests**

Cover:

```ts
test("dedupes by eventId")
test("applies events in arrival order")
test("does not read seq")
test("does not read cursor")
test("message.completed replaces accumulated delta")
test("run.completed status=cancelled closes streaming")
test("malformed event is skipped without crashing")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-web
bun test tests/session-reducer.test.ts
```

- [ ] **Step 3: Remove seq/cursor from domain state**

Keep arrival order as array append order. If UI needs a local key, use local
render id, not server ordering semantics.

- [ ] **Step 4: Reset old local cache instead of compatibility shims**

If old localStorage schema includes `lastResumeId`, `seq`, or `cursor`, discard
that cache and load snapshot. Do not preserve a long compatibility path.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd kokoro-web
bun test tests/session-reducer.test.ts
bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git -C kokoro-web add src tests
git -C kokoro-web commit -m "fix: render session events without cursor ordering"
```

---

## Chunk 4: Agent DeepAgents Runtime Cleanup

### Task 4.1: AgentRunInput Contract

**Files:**

- Create: `kokoro-agent/src/kokoro_agent/domain/agent_run_input.py`
- Create: `kokoro-agent/src/kokoro_agent/domain/backend_policy.py`
- Create: `kokoro-agent/tests/test_agent_run_input.py`

- [ ] **Step 1: Write failing Python tests**

Cover:

```py
def test_agent_run_input_requires_identity_fields(): ...
def test_agent_run_input_carries_context_package_not_session_db_ref(): ...
def test_backend_policy_rejects_local_shell_in_production(): ...
def test_backend_policy_accepts_state_local_shell_e2b_custom(): ...
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_agent_run_input.py -q
```

- [ ] **Step 3: Implement Pydantic models**

Use Pydantic models with explicit fields:

```py
class AgentRunInput(BaseModel):
    site_id: str
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str
    run_id: str
    user_id: str
    input_message_id: str
    assistant_message_id: str
    context: RunContext
    model_runtime: ModelRuntime
    permission_mode: PermissionMode
    backend_policy: BackendPolicy
    enabled_skills: list[SkillRef] = []
    enabled_mcp_servers: list[McpServerRef] = []
    enabled_tools: list[str] = []
    trace_context: TraceContext
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_agent_run_input.py -q
uv run mypy src tests
uv run ruff check src tests
```

- [ ] **Step 5: Commit**

```bash
git -C kokoro-agent add src tests
git -C kokoro-agent commit -m "feat: add agent run input contract"
```

### Task 4.2: DeepAgents Backend And HITL

**Files:**

- Create: `kokoro-agent/src/kokoro_agent/infrastructure/deepagents_runtime.py`
- Create: `kokoro-agent/src/kokoro_agent/infrastructure/backend_config.py`
- Create: `kokoro-agent/src/kokoro_agent/application/approval_flow.py`
- Create: `kokoro-agent/tests/test_deepagents_runtime.py`
- Create: `kokoro-agent/tests/test_approval_flow.py`

- [ ] **Step 1: Write failing runtime tests**

Cover:

```py
def test_state_backend_is_production_default(): ...
def test_local_shell_is_rejected_in_production(): ...
def test_e2b_backend_fails_loud_when_dependency_missing(): ...
def test_hitl_resume_preserves_action_request_order(): ...
def test_runtime_subagent_creation_is_gated(): ...
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_deepagents_runtime.py tests/test_approval_flow.py -q
```

- [ ] **Step 3: Implement backend config**

Rules:

```text
production default: state
development/test default: local_shell
local_shell in production: hard error
e2b missing package/key: hard error
custom missing implementation: hard error
S3/object storage: artifact storage only, not execute backend
```

- [ ] **Step 4: Implement HITL mapping**

Use DeepAgents/LangChain semantics:

```text
HumanInTheLoopMiddleware / interrupt_on
checkpointer + thread_id
action_requests order preserved
approve / reject / edit / respond mapped to resume command
cancel mapped to run cancellation
```

- [ ] **Step 5: Disable implicit dynamic subagents**

Explicitly replace or disable default `general-purpose` and dynamic subagent
creation. Runtime creation becomes `propose_subagent` and requires policy/HITL.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_deepagents_runtime.py tests/test_approval_flow.py -q
uv run mypy src tests
uv run ruff check src tests
```

- [ ] **Step 7: Commit**

```bash
git -C kokoro-agent add src tests
git -C kokoro-agent commit -m "feat: configure deepagents runtime"
```

### Task 4.3: Tool Naming And Event Projection

**Files:**

- Modify: `kokoro-agent/src/kokoro_agent/infrastructure/tools/web_fetch.py`
- Modify: `kokoro-agent/src/kokoro_agent/infrastructure/tools/now.py`
- Create or modify: `kokoro-agent/src/kokoro_agent/application/event_projection.py`
- Create: `kokoro-agent/tests/test_raw_events.py`

- [ ] **Step 1: Write failing event/tool tests**

Cover:

```py
def test_web_fetch_tool_name_is_stable(): ...
def test_now_uses_user_timezone_from_run_input(): ...
def test_run_cancel_maps_to_run_completed_status_cancelled(): ...
def test_timeout_maps_to_run_completed_status_timeout(): ...
def test_no_run_cancelled_event_kind_is_emitted(): ...
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_raw_events.py -q
```

- [ ] **Step 3: Implement projection**

Raw event kinds allowed:

```text
run.started
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

- [ ] **Step 4: Remove second tool-state source**

Do not introduce `kokoro_agent.tool_state` unless it is a private LangGraph
checkpoint implementation detail. Web-visible tool state comes from session
events.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd kokoro-agent
uv run pytest tests/test_raw_events.py -q
uv run mypy src tests
uv run ruff check src tests
```

- [ ] **Step 6: Commit**

```bash
git -C kokoro-agent add src tests
git -C kokoro-agent commit -m "fix: normalize agent raw events"
```

---

## Chunk 5: Cross-Repo Integration

### Task 5.1: Contract Drift Checks

**Files:**

- Modify: `docs/kokoro-handbook/operations/testing-checklist.md`

- [ ] **Step 1: Document checks**

Checks must fail on:

```text
AgentExecutionManifest
fetch_url
run.cancelled event kind
run.timeout event kind
tool_state as public state
kokoro-session SQLite runtime
Web lastResumeId product state
Web seq/cursor sort
```

- [ ] **Step 2: Run checks and verify RED if old code remains**

Run:

```bash
PATTERN="AgentExecutionManifest|fetch_url|run.cancelled|run.timeout"
PATTERN="$PATTERN|tool_state|lastResumeId|sqlite"
rg -n "$PATTERN" docs/kokoro-handbook kokoro-agent kokoro-session kokoro-web
```

- [ ] **Step 3: Fix all failing drift points**

Only edit the three subrepos or handbook docs.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PATTERN="AgentExecutionManifest|fetch_url|run.cancelled|run.timeout"
PATTERN="$PATTERN|tool_state|lastResumeId|sqlite"
rg -n "$PATTERN" docs/kokoro-handbook kokoro-agent kokoro-session kokoro-web
```

- [ ] **Step 5: Commit**

```bash
git add docs/kokoro-handbook/operations/testing-checklist.md
git commit -m "docs: add three-repo runtime drift checks"
```

### Task 5.2: End-To-End Runtime Smoke

**Files:**

- Create: `kokoro-session/tests/e2e-agent-session-web.test.ts` or equivalent
- Update package scripts only if needed

- [ ] **Step 1: Write failing e2e smoke**

Cover:

```text
POST /sessions/:id/messages
agent emits raw message/tool/terminal events
session stores Mongo projections
SSE sends browser-facing events
web reducer applies snapshot + events
refresh uses snapshot + attach without duplicates
```

- [ ] **Step 2: Run e2e and verify RED**

Run:

```bash
cd kokoro-session
bun test tests/e2e-agent-session-web.test.ts
```

- [ ] **Step 3: Implement minimal test harness**

Use fakes for agent/web where possible. Use Mongo/Redis integration only when
services are available; otherwise skip cleanly.

- [ ] **Step 4: Verify all three repos**

Run:

```bash
cd kokoro-session && bun test && bun run typecheck && bun run lint
cd ../kokoro-web && bun test && bun run typecheck
cd ../kokoro-agent
uv run pytest
uv run mypy src tests
uv run ruff check src tests
```

- [ ] **Step 5: Commit**

```bash
git -C kokoro-session add tests src package.json
git -C kokoro-session commit -m "test: add runtime smoke"
git -C kokoro-web add tests src package.json
git -C kokoro-web commit -m "test: add session runtime smoke"
git -C kokoro-agent add tests src
git -C kokoro-agent commit -m "test: add agent runtime smoke"
```

If the root repository tracks these as submodules, update root gitlinks only
after the subrepo commits exist:

```bash
git add kokoro-agent kokoro-session kokoro-web
git commit -m "chore: update three runtime submodules"
```

---

## Final Verification

- [ ] `kokoro-session`: `bun test`
- [ ] `kokoro-session`: `bun run typecheck`
- [ ] `kokoro-session`: `bun run lint`
- [ ] `kokoro-web`: `bun test`
- [ ] `kokoro-web`: `bun run typecheck`
- [ ] `kokoro-agent`: `uv run pytest`
- [ ] `kokoro-agent`: `uv run mypy src tests`
- [ ] `kokoro-agent`: `uv run ruff check src tests`
- [ ] `npx markdownlint-cli2 "docs/kokoro-handbook/**/*.md"`
- [ ] drift scan:

```bash
PATTERN="AgentExecutionManifest|fetch_url|run.cancelled|run.timeout"
PATTERN="$PATTERN|tool_state|lastResumeId|sqlite"
rg -n "$PATTERN" docs/kokoro-handbook kokoro-agent kokoro-session kokoro-web
```

Allowed hits must only be explicit prohibition notes.

## Rollout Notes

- Merge order should be session first, web second, agent third only if using
  separate branches. If implementing in one branch, keep commits chunked.
- Do not preserve old `/runs?input=` API unless the user explicitly asks for a
  migration window. Current goal is clean V1, not compatibility.
- Do not add PostgreSQL, `kokoro-contracts`, or `ports` directories.
- Do not reintroduce session SQLite runtime.
