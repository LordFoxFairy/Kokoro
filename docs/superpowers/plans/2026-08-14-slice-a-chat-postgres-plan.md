# Slice A Chat PostgreSQL Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before a lane starts, its next milestone MUST be expanded into a separately reviewed JIT implementation cut with exact files, actual RED test/code, self-contained commands and one precise commit; workers never invent omitted code from this roadmap.

**Goal:** Replace `kokoro-session` Mongo persistence and cross-owner orchestration with the `kokoro-chat` PostgreSQL owner while preserving Conversation/Message/projection/recovery/SSE/HITL behavior.

**Architecture:** `kokoro-chat` owns Conversation, Message/Part, RunLaunch/RunView, Interaction, owner receipts, projection inbox/DLQ and browser stream tail. Each command is one PostgreSQL transaction through a Chat UnitOfWork. Agent, IAM, Capability and Model are accessed only through generated clients; Chat no longer owns billing, model/capability resolution, workspace or artifacts.

**Tech Stack:** Node.js 22+, TypeScript 5, Prisma Client PostgreSQL, `pg`, Connect RPC, Protobuf-ES, Redis Streams, HTTP/SSE, Vitest.

## Global Constraints

- Work only in `/tmp/kokoro-chat-slice-a`, derived from `kokoro-session@4f4aa3defc5cce79be58c447d7f053c6204ef48f`.
- Root owns `30-chat.sql` and the generated Chat-only Prisma schema; Chat does not contain migrations.
- Preserve event identity, epoch/producer sequence, durable-first projection, gap/DLQ, terminal convergence, control outbox and SSE replay→live handoff.
- Owner receipt identity is `(organization_id, command_id)` plus canonical request digest.
- Complete snapshot is a repeatable-read query over normalized owner rows plus watermark; events before watermark may expire.
- No auto-steer when Submit sees an active run; return a typed conflict.
- No billing, Hub, Model, Capability, delivery, file or object-store owner logic remains in the Chat runtime.
- Every application call authorizes before touching owner state: CreateConversation=`chat.conversation.create`, ListConversations=`chat.conversation.list`, ReadConversationSnapshot and StreamConversationEvents=`chat.conversation.read`, SubmitMessage=`chat.message.submit`, DecideInteraction=`chat.interaction.decide`. Stream verifies Web workload token, JWT and IAM authorization before reading the retention floor or emitting any frame; wrong/cross-organization callers receive zero frames. It schedules an authentication deadline at JWT `exp + 30s`, emits nothing after it and closes the HTTP/2 stream.
- Chat listens on 7205, accepts only the Web workload token on owner RPC/SSE, verifies the accompanying IAM access JWT through JWKS, and derives ActorContext from verified claims. Chat uses its own workload token for IAM and Agent calls; request bodies cannot supply identity axes.

---

### Milestone 1: Extract Chat domain types from the collection port

**Files:**
- Create: `src/domain/identity.ts`, `command.ts`, `conversation.ts`, `message.ts`, `message-part.ts`, `run.ts`, `interaction.ts`, `control.ts`, `projection.ts`
- Modify: `package.json`, `package-lock.json`, `src/store/port.ts`
- Test: `tests/domain/command.test.ts`, `conversation.test.ts`, `interaction.test.ts`, `projection.test.ts`

**Interfaces:**
- Produces shared domain types used by application commands and persistence.

**JIT cut requirement 1 — Install the committed local toolchain**

```bash
(cd /tmp/kokoro-chat-slice-a && \
  npm pkg set name=kokoro-chat && \
  npm install --package-lock-only --ignore-scripts && \
  npm ci && test -x ./node_modules/.bin/vitest)
```

Hard-cut `package.json.name` from `kokoro-session` to `kokoro-chat`, refresh `package-lock.json`, and add a domain test that rejects the old name in package/export/deployable metadata. The candidate contains committed `package-lock.json`; `npm ci` must complete before any test command, and `test -x ./node_modules/.bin/vitest` is required. Every direct test invocation uses that lockfile-installed binary, so a missing local install fails rather than reading npm cache or registry. Task 2 updates dependencies with exact versions and commits the refreshed lock.

**JIT cut requirement 2 — Write failing domain tests**

Implement four non-empty cases:

1. Hash `{conversationId,text,model}` in two key orders and assert byte-identical digest; change `text` and assert a different digest.
2. Construct a terminal Interaction, apply `pending`, and assert `INTERACTION_STATE_INVALID` with the original object unchanged.
3. Apply producer `(epoch=2,seq=8)` after `(2,9)` and assert `PROJECTION_SEQUENCE_REGRESSION`.
4. Parse actor/conversation IDs with deliberately swapped UUIDs and assert the branded constructors and runtime validators reject the swap.

**JIT cut requirement 3 — Run RED**

```bash
cd /tmp/kokoro-chat-slice-a
./node_modules/.bin/vitest run tests/domain
```

**JIT cut requirement 4 — Implement the core identities**

```ts
export type ActorContext = Readonly<{
  principalId: string
  siteId: string
  organizationId: string
}>

export type CommandIdentity = Readonly<{
  commandId: string
  requestDigest: string
}>

export type StreamCursor = Readonly<{
  conversationId: string
  seq: bigint
}>
```

Move semantic types from `src/store/port.ts`; leave no Mongo document or collection type in `src/domain`.

**JIT cut requirement 5 — Run GREEN and commit**

```bash
cd /tmp/kokoro-chat-slice-a
./node_modules/.bin/vitest run tests/domain
npm run typecheck
git -C /tmp/kokoro-chat-slice-a add src/domain src/store/port.ts tests/domain
git -C /tmp/kokoro-chat-slice-a commit -m "refactor(chat): extract owner domain types"
```

### Milestone 2: Define the Chat UnitOfWork and PostgreSQL repositories

**Files:**
- Add generated consumer closure already emitted by Root: `src/generated/**`, `src/generated/provenance.json`
- Create: `src/application/ports/chat-unit-of-work.ts`, `authorization.ts`, `agent-runtime.ts`
- Create: `src/infrastructure/iam/connect-iam-authorization-client.ts`
- Create: `src/persistence/postgres/client.ts`, `chat-unit-of-work.ts`, `command-repository.ts`, `conversation-repository.ts`, `message-repository.ts`, `run-repository.ts`, `interaction-repository.ts`, `projection-repository.ts`, `outbox-repository.ts`, `stream-repository.ts`
- Create: `tests/persistence/postgres/chat-unit-of-work.pg.test.ts`, `chat-schema-negative.pg.test.ts`, `tests/infrastructure/iam-authorization-client.test.ts`
- Modify: `package.json`, `.env.example`
- Create: `tsconfig.build.json`, `Dockerfile`

**Interfaces:**
- Produces: `ChatUnitOfWork.run(isolation, callback)` and transaction-scoped repositories.

**JIT cut requirement 1 — Write a failing rollback/ownership suite**

Implement six live cases:

1. In one UoW insert receipt/message then throw an injected error; query from another connection and assert both counts are zero.
2. Claim `(organization,command,digest)` twice; assert one receipt ID and the stored result on replay.
3. Reclaim the same pair with a second digest; assert `COMMAND_DIGEST_CONFLICT` and one row total.
4. Import the generated Prisma type/model registry and assert its sorted model set equals the 14 Chat names.
5. Hold two transactions at the allocation barrier, release together, commit both and assert consecutive unique sequence values; repeat with one rollback and assert the rolled-back value is reusable/no committed gap.
6. Start a real IAM generated handler, call it through `ConnectIamAuthorizationClient`, and assert exact permission/actor fields plus Web/Chat workload-token rejection; the Chat client never receives a Prisma/transaction object.

**JIT cut requirement 2 — Run RED against a fresh Root baseline**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-uow-red --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/persistence/postgres)
```

**JIT cut requirement 3 — Implement transaction-scoped ports**

```ts
export type Isolation = "Serializable" | "RepeatableRead"

export interface ChatUnitOfWork {
  run<T>(isolation: Isolation, work: (tx: ChatTransaction) => Promise<T>): Promise<T>
}

export interface ChatTransaction {
  commands: CommandRepository
  conversations: ConversationRepository
  messages: MessageRepository
  runs: RunRepository
  interactions: InteractionRepository
  projections: ProjectionRepository
  outboxes: OutboxRepository
  streams: StreamRepository
}
```

Use Prisma for typed CRUD and `$queryRaw` only for registered `FOR UPDATE`, generation CAS and stream-sequence allocation queries.

Add exact `@connectrpc/connect@2.1.2`, `@connectrpc/connect-node@2.1.2`, `@connectrpc/connect-fastify@2.1.2`, `@bufbuild/protobuf@2.14.0`, `@prisma/client@6.19.3`, `prisma@6.19.3` and `pg@8.23.0`; use the generated Chat-only Prisma schema and the existing Prisma 6 lifecycle. The schema uses standard `node_modules/@prisma/client` output because Chat has exactly one owner schema. Chat's Agent adapter uses `createGrpcTransport`; Web uses Connect. Do not add a child migration command or a Prisma upgrade.

```bash
(cd /tmp/kokoro-chat-slice-a && \
  npm install --save-exact @connectrpc/connect@2.1.2 @connectrpc/connect-node@2.1.2 \
    @connectrpc/connect-fastify@2.1.2 @bufbuild/protobuf@2.14.0 @prisma/client@6.19.3 pg@8.23.0 && \
  npm install --save-dev --save-exact prisma@6.19.3)
```

`ConnectIamAuthorizationClient` is the only IAM application-port adapter. It calls generated `IamAuthorizationService.Authorize` over Connect with the Chat workload token and returns the generated allow/deny result; no IAM repository or SQL model is imported into Chat. Verify `src/generated/provenance.json` against the frozen Root contract commit before compiling.

Add exact scripts `test:integration: "vitest run tests/integration tests/persistence/postgres"`, `build: "tsc -p tsconfig.build.json"`, and make production `start` execute only `node dist/main.js`. `tsconfig.build.json` includes production `src/**` and excludes tests/old Mongo paths. The multi-stage Dockerfile runs `npm ci`, Root-generated Prisma client generation and `npm run build`, copies production `node_modules` including Prisma's native engine into the final stage, then starts the compiled entry as a non-root user. The Root backend Compose E2E starts this exact final image and calls a real Chat query; a build-only image does not satisfy the release gate.

**JIT cut requirement 4 — Run GREEN and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-uow-green --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/persistence/postgres)
cd /tmp/kokoro-chat-slice-a
npm run typecheck && npm run lint
git -C /tmp/kokoro-chat-slice-a add package.json package-lock.json prisma tsconfig.build.json Dockerfile src/generated src/application/ports src/infrastructure/iam src/persistence tests/persistence tests/infrastructure .env.example
git -C /tmp/kokoro-chat-slice-a commit -m "feat(chat): add PostgreSQL unit of work"
```

### Milestone 3: Implement CreateConversation

**Files:**
- Create: `src/application/create-conversation.ts`
- Create: `tests/application/create-conversation.test.ts`

**Interfaces:**
- Consumes: IAM `Authorize`; produces a stable Conversation ID and opaque Agent namespace directly under an Organization.

**JIT cut requirement 1 — Write RED tests**

Implement these concrete tests:

- Authorize one actor, execute `CreateConversation`, then assert one conversation with matching Site/organization/creator and one opaque namespace; assert no Project row or Project RPC exists.
- Execute it again with the same `(organization,command,digest)` and assert the exact conversation/generation plus `replayed=true`; drift must conflict.
- Use an IAM fake that records calls and a Chat DB probe; assert IAM only receives `Authorize` and no IAM adapter receives a Chat transaction/client.
- Inject failure after Conversation insert but before receipt result; assert both roll back and no stream row exists.
- Supply actor Site/organization claims that do not match and assert `CONVERSATION_SCOPE_MISMATCH` before any Conversation row is written.

**JIT cut requirement 2 — Implement the exact command signature**

```ts
export interface CreateConversation {
  execute(input: {
    actor: ActorContext
    command: CommandIdentity
    title: string
  }): Promise<{
    conversationId: string
    agentNamespace: string
    generation: bigint
    watermark: bigint
    replayed: boolean
  }>
}
```

Call IAM `Authorize(permission="chat.conversation.create")` before opening the Chat transaction. The transaction claims the organization-scoped receipt, inserts `chat_conversation` with `organization_id`, `site_id`, creator and opaque namespace, fills the receipt result and commits with watermark `0` (or the existing current watermark on replay). It emits no browser event because the mature envelope requires a nonempty browser run ID; first `session.created` is synthesized by the first Submit using that transaction's launch ID. Project is not read or created.

**JIT cut requirement 3 — Run GREEN and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-create-conversation --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/application/create-conversation.test.ts)
git -C /tmp/kokoro-chat-slice-a add src/application/create-conversation.ts tests/application/create-conversation.test.ts
git -C /tmp/kokoro-chat-slice-a commit -m "feat(chat): create conversations atomically"
```

### Milestone 4: Replace `start-message.ts` with one Submit transaction

**Files:**
- Create: `src/application/submit-message.ts`
- Modify then delete after parity: `src/relay/start-message.ts`
- Create: `tests/application/submit-message.test.ts`
- Port behavior from: `tests/store-behaviour.ts`, `tests/relay.test.ts`, `tests/r0-fault-matrix.test.ts`

**Interfaces:**
- Produces receipt, user/assistant messages, launch, active slot, launch outbox and stream event.

**JIT cut requirement 1 — Write RED tests for atomic Submit**

Implement the Submit matrix with database assertions:

- First success: query by receipt ID and assert one receipt, two messages with required parts, one launch, one active slot, one launch outbox and exactly three consecutive browser events: `session.created`, `run.created`, `message.user`, all using `run_id=launch_id`.
- Later success in a Conversation whose first launch is terminal appends exactly `run.created` and `message.user`; it never repeats `session.created`.
- Inject failure at every repository write boundary in a parameterized test and assert zero rows for that command after rollback.
- Repeat the same organization/command/digest and assert identical IDs, one row per effect and `replayed=true`.
- Change text/model while reusing the command ID and assert `COMMAND_DIGEST_CONFLICT` plus unchanged prior rows.
- Barrier two serializable submissions for the same idle Conversation; assert one success and one `ACTIVE_RUN_CONFLICT`.
- Submit while a Conversation active slot exists and assert no control/steer row was created.

**JIT cut requirement 2 — Implement the command**

```ts
export interface SubmitMessage {
  execute(input: {
    actor: ActorContext
    conversationId: string
    command: CommandIdentity
    text: string
    requestedModelLabel?: string
    requestedAgentKey?: string
  }): Promise<{
    receiptId: string
    userMessageId: string
    assistantMessageId: string
    launchId: string
    launchState: "waiting"
    conversationGeneration: bigint
    watermark: bigint
    replayed: boolean
  }>
}
```

Do not call Capability, Model or Billing in this command. Resolve omitted selectors locally to model label `default` and Agent preset key `general` before persistence; persist and digest those exact values. Chat rejects malformed selector syntax, while syntactically valid unknown values pass to Agent admission, deterministically fail there and converge through `RecordAdmissionFailure`. Serializable active-slot locking plus the owner receipt protect concurrent Submit; the browser carries no Conversation generation. `chat_launch_outbox` is the only after-commit launch intent.

**JIT cut requirement 3 — Remove the replaced relay and run GREEN**

Delete `src/relay/start-message.ts` after its callers have been switched to `SubmitMessage`; an architecture test must reject imports of the old relay.

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-submit --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/application/submit-message.test.ts tests/relay.test.ts tests/r0-fault-matrix.test.ts)
cd /tmp/kokoro-chat-slice-a
git -C /tmp/kokoro-chat-slice-a add -A src/application/submit-message.ts src/relay/start-message.ts src tests
git -C /tmp/kokoro-chat-slice-a commit -m "feat(chat): make message submit atomic"
```

### Milestone 5: Port projection, terminal and control semantics

**Files:**
- Create: `src/application/project-agent-event.ts`, `decide-interaction.ts`
- Modify: `src/relay/envelope.ts`, `projection.ts`, `durable.ts`, `control.ts`
- Test: `tests/application/project-agent-event.test.ts`, `decide-interaction.test.ts`
- Port: `tests/durable-watermark.test.ts`, `control.test.ts`, `control-outbox.test.ts`, `finalization-reconciler.test.ts`

**Interfaces:**
- Consumes generated Agent event envelope; produces projection/stream rows and post-commit Agent ack.

**JIT cut requirement 1 — Write RED tests**

Cover duplicate event, epoch/seq gap, schema DLQ without fake terminal, message-part projection, four HITL kinds, decision generation/action digest, terminal active-slot release and no terminal revival.

**JIT cut requirement 2 — Implement projection result**

```ts
export type ProjectionResult =
  | { status: "projected"; conversationId: string; watermark: bigint }
  | { status: "duplicate" }
  | { status: "gap" }
  | { status: "dlq" }
```

Inbox claim, RunView/MessagePart/Interaction update and stream event are one transaction. Agent ack happens after commit and is retried from local evidence.

`ReadConversationSnapshot` does not wait for Agent admission. When `chat_active_run` and `chat_run_launch` exist but projector-owned `chat_run_view` does not, it synthesizes the stable active view from `launch_id` with state `PREPARING`, zero received/projected sequence and absent `agent_run_id`; it never invents an Agent identity. Once admission succeeds, projected Agent fields fill the same launch view. A test pauses the launch worker immediately after Submit commit, restarts Chat, proves the snapshot still exposes the active launch and blocks a second Submit, then proves admission failure or terminal projection removes it.

**JIT cut requirement 3 — Implement Control**

Receipt claim, Interaction CAS, ControlCommand, ControlOutbox and browser event are one transaction. Same command replay returns the same Control ID.

**JIT cut requirement 4 — Run GREEN and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-projection-control --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run \
    tests/application/project-agent-event.test.ts \
    tests/application/decide-interaction.test.ts \
    tests/durable-watermark.test.ts \
    tests/control.test.ts \
    tests/control-outbox.test.ts \
    tests/finalization-reconciler.test.ts)
cd /tmp/kokoro-chat-slice-a
git -C /tmp/kokoro-chat-slice-a add src/application src/relay tests
git -C /tmp/kokoro-chat-slice-a commit -m "feat(chat): project Agent facts through PostgreSQL"
```

### Milestone 6: Expose exact Chat Connect/gRPC services plus watermark-tail stream RPC

**Files:**
- Create: `src/application/read-conversation-snapshot.ts`
- Create: `src/interfaces/connect/chat-command-service.ts`, `chat-query-service.ts`, `routes.ts`, `interceptors.ts`
- Modify: `src/http/sse.ts`, `src/http/server.ts`, `src/http/format.ts`
- Create: `src/http/routes/events.ts`, `health.ts`
- Test: `tests/application/read-conversation-snapshot.test.ts`, `tests/interfaces/chat-connect.test.ts`, `tests/http-snapshot-tail.test.ts`
- Port: `tests/http.test.ts`, `tests/sse.test.ts`

**Interfaces:**
- Produces the exact generated `ChatCommandService`/`ChatQueryService`, a complete snapshot and opaque `after_seq` cursor.

**JIT cut requirement 1 — Write the retention RED test**

The test creates messages/parts/run/interaction and events, reads a snapshot, deletes all `chat_stream_event` rows at or below its watermark, restarts the Chat process, reads again and expects the same historical messages/parts and pending interaction before consuming new tail events.

**JIT cut requirement 2 — Implement one repeatable-read snapshot**

```ts
export type ConversationSnapshot = {
  conversation: Conversation
  messages: Array<Message & { parts: MessagePart[] }>
  activeRun: RunView | null
  pendingInteractions: Interaction[]
  watermark: bigint
}
```

Read all rows and `next_stream_seq - 1` in the same repeatable-read transaction. Generated server-streaming `StreamConversationEvents` requires `after_seq`; it replays only `seq > after_seq`, then switches to the existing live bus without a gap. A stale cursor fails with typed `SNAPSHOT_REQUIRED` before the first frame. A fake-clock test opens with a valid JWT, advances beyond `exp + 30s`, proves zero later frames and stream close, then refreshes and resumes from the original last sequence without loss or duplication.

Before streaming, compare `after_seq` with the retained minimum and current `next_stream_seq`. If the cursor predates a deleted range, return typed HTTP 409 `SNAPSHOT_REQUIRED` without emitting a partial tail. A cursor at the current watermark with no rows is valid.

**JIT cut requirement 3 — Register an exact RPC inventory**

`ChatCommandService` exposes only `CreateConversation`, `SubmitMessage` and `DecideInteraction`. `ChatQueryService` exposes only `ReadConversationSnapshot`, `ListConversations` and server-streaming `StreamConversationEvents`. The interceptor first verifies the Web workload token, then verifies the user access JWT against IAM JWKS and creates `ActorContext`; request bodies cannot override principal/Site/organization identity. Tests call every method with valid, missing and wrong workload tokens plus forged/expired/cross-Site JWTs. The same HTTP/2-capable 7205 listener serves generated Connect and gRPC protocols plus health/readiness—no internal `/v1` SSE route, legacy REST mutation route or catch-all. A Python generated root-e2e client must complete the stream interoperability test against this TypeScript listener.

**JIT cut requirement 4 — Run GREEN and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-snapshot-tail --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/application/read-conversation-snapshot.test.ts tests/interfaces/chat-connect.test.ts tests/http-snapshot-tail.test.ts tests/http.test.ts tests/sse.test.ts)
cd /tmp/kokoro-chat-slice-a
git -C /tmp/kokoro-chat-slice-a add src/application/read-conversation-snapshot.ts src/interfaces/connect src/http tests
git -C /tmp/kokoro-chat-slice-a commit -m "feat(chat): expose owner RPC and snapshot tail"
```

### Milestone 7: Replace recovery workers and composition

**Files:**
- Create: `src/recovery/launch-outbox-worker.ts`, `control-outbox-worker.ts`, `projection-reconciler.ts`, `stream-retention-worker.ts`
- Create: `src/infrastructure/agent/grpc-agent-runtime-client.ts`, `src/infrastructure/iam/jwks-client.ts`
- Modify: `src/relay/recover.ts`, `finalization-reconciler.ts`, `dispatch-reconciler.ts`, `control-outbox-scanner.ts`, `relay-run.ts`, `src/main.ts`, `src/config.ts`, `src/store/factory.ts`, `.env.example`
- Test: `tests/recovery/launch-outbox-worker.test.ts`, `projection-reconciler.test.ts`, `stream-retention-worker.test.ts`, existing `recover.test.ts`, `dispatch-reconciler.test.ts`, `main.test.ts`

**Interfaces:**
- Consumes Agent generated client and Redis event transport; produces at-least-once launch/control delivery and monotonic projection ack.

**JIT cut requirement 1 — Write lifecycle RED tests**

Test startup failure rollback, unready before PG/Agent checks, stop-claim/drain before listener and DB close, generated gRPC request/response interoperability with the Python Agent server, launch retry until Agent acceptance, exact `launch_request_digest` replay/drift behavior, control retry until Agent receipt, recovery of an active run after restart, and retention deleting only expired stream rows. Exact production config is `0.0.0.0:7205`, IAM/Agent endpoints, `DATABASE_URL_KOKORO_APP`, Redis URL and Web/Chat workload token files; missing files fail before opening the listener. After retention, a stale cursor must receive `SNAPSHOT_REQUIRED` and a fresh snapshot watermark must resume normally.

**JIT cut requirement 2 — Implement workers over Chat tables**

Workers claim rows with `FOR UPDATE SKIP LOCKED`, use bounded leases and update only their outbox/reconciliation states. They do not write Agent tables. `LaunchOutboxWorker` loads the committed Conversation, user MessagePart and RunLaunch, then builds exactly one generated `LaunchRunRequest`: `launch_id`, canonical `launch_request_digest`, `message_id`, immutable text `content`, Conversation `agent_namespace`, `session_id=conversation_id`, `thread_id=conversation_id`, `site_id`, `organization_id`, requested preset/model/capability selectors. The digest covers that complete canonical envelope; same launch/same digest replays, any field drift conflicts. No Project field exists. The retention worker deletes expired `chat_stream_event` rows in bounded batches; normalized Message/Part/RunView/Interaction rows are never retention targets.

If Agent returns deterministic `ADMISSION_FAILED`, `RecordAdmissionFailure` locks the RunLaunch/active slot/assistant placeholder and atomically marks launch plus assistant failed, removes `chat_active_run`, and appends one synthetic browser `run.failed` with `agent_admission_rejected`. Duplicate response and worker restart replay the same terminal fact without a second event. Tests cover rejection, replay, digest drift and restart recovery. A pending interaction persists its complete immutable bounded `payload` in `chat_interaction`; snapshot reconstruction never depends on retained stream rows. The projector follows the machine manifest's exhaustive 21-kind materialization map into Message/Part, RunView and Interaction facts. Retention tests cover text, tool, todo, subagent and pending interaction, and prove unknown/uncommitted kinds are not deleted.

**JIT cut requirement 3 — Run GREEN and commit**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-recovery --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/recovery tests/recover.test.ts tests/dispatch-reconciler.test.ts tests/main.test.ts)
cd /tmp/kokoro-chat-slice-a
git -C /tmp/kokoro-chat-slice-a add src/recovery src/relay src/infrastructure/agent src/infrastructure/iam src/main.ts src/config.ts src/store tests .env.example
git -C /tmp/kokoro-chat-slice-a commit -m "refactor(chat): recover through owner outboxes"
```

### Milestone 8: Delete old owner violations and Mongo authority

**Files:**
- Delete: `src/store/mongo.ts`, `src/billing/**`, `src/hub/**`, `src/namespace/**`, `src/deliveries/**`, `src/workspace/**`, `src/contract/storage.ts`
- Modify: `package.json`, `.env.example`, `README.md`, `src/store/INDEX.md`, `src/http/INDEX.md`, `src/relay/INDEX.md`
- Delete/move tests: billing, capability snapshot, hub resolver, namespace, deliveries, workspace tests.

**JIT cut requirement 1 — Add the zero-call RED gate**

Create `tests/architecture/owner-boundary.test.ts` that scans production imports/config/package dependencies and rejects `mongodb`, Hub/Billing/Workspace owner imports, `KOKORO_MONGO_`, shared collection names and direct Model/Capability/Credit/Artifact clients.

**JIT cut requirement 2 — Run RED, remove old paths, run GREEN**

```bash
cd /tmp/kokoro-chat-slice-a
./node_modules/.bin/vitest run tests/architecture/owner-boundary.test.ts
npm uninstall mongodb @aws-sdk/client-s3
./node_modules/.bin/vitest run tests/architecture/owner-boundary.test.ts
```

**JIT cut requirement 3 — Run full Chat gates**

```bash
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
(cd /tmp/kokoro-chat-slice-a && \
  npm run check:no-bun && npm run typecheck && npm run build && npm run lint && npm test && \
  docker build -t kokoro-chat:slice-a . && git diff --check)
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-full --cwd /tmp/kokoro-chat-slice-a -- \
  ./node_modules/.bin/vitest run tests/persistence/postgres tests/integration)
```

**JIT cut requirement 4 — Request independent review, commit the hard cut and freeze**

Review must verify transaction boundaries, snapshot retention, terminal non-revival, owner zero-call and no behavior-suite deletion used to hide a regression. After P0/P1/P2 are zero:

```bash
git -C /tmp/kokoro-chat-slice-a add -A -- src package.json package-lock.json prisma Dockerfile tsconfig.build.json .env.example README.md tests
git -C /tmp/kokoro-chat-slice-a diff --cached --check
git -C /tmp/kokoro-chat-slice-a commit -m "refactor(chat): hard cut conversation authority to PostgreSQL"
test -z "$(git -C /tmp/kokoro-chat-slice-a status --short)"
```

Root renames/promotes the submodule only in the final plan.
