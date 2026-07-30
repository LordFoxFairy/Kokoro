# Model Gateway Resumable Streaming Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one durable, resumable, encrypted Model Gateway provider stream without changing GA semantics or creating a user-visible Job.

**Architecture:** Root adds a closed Connect server-streaming contract and registry operation. Platform adds a PostgreSQL queued/owner-fenced invocation journal, an internal dispatcher, a bounded LiteLLM SSE adapter, and unary compatibility over the same invocation.

**Tech Stack:** Protobuf/Buf Validate, ConnectRPC 2, TypeScript 5.9, Node 24 Web Streams, PostgreSQL, AES-256-GCM, Vitest.

---

## Chunk 1: Root contract

### Task 1: Lock the server-streaming wire shape

**Files:**
- Modify: `contract/proto/kokoro/platform/model/v1/model_gateway.proto`
- Modify: `contract/tests/test_buf_contract.py`
- Modify: `contract/registry/boundaries.yaml`
- Test: `scripts/contract/check-boundary-registry.mjs`

- [ ] Write failing Proto source tests for `StreamModel`, `after_sequence`, closed frame payloads, strict bounds, sequence and digest chain fields.
- [ ] Run the focused Python test and confirm the method/frames are absent.
- [ ] Add the typed server-streaming messages without changing existing unary field numbers.
- [ ] Register `StreamModel` as a same-identity effect operation whose receipt is the frame invocation reference.
- [ ] Run Buf lint, Proto tests, and boundary registry checks.

### Task 2: Generate the Platform provider mirror

**Files:**
- Regenerate in Platform: `src/interfaces/connect/generated-model-gateway/kokoro/platform/model/v1/model_gateway_pb.ts`
- Regenerate in Platform: `src/interfaces/connect/generated-model-gateway/contract-metadata.ts`

- [ ] Run the Root-owned pinned Buf generator into the Platform worktree.
- [ ] Prove the generated service method has `methodKind: server_streaming` and no hand edits.

## Chunk 2: Platform durable owner

### Task 3: Add fresh-only journal and dispatch ownership schema

**Files:**
- Create: `prisma/migrations/20260803_1200_model_gateway_resumable_stream/migration.sql`
- Modify: `test/architecture/model-gateway-schema.test.ts`
- Modify: `src/infrastructure/postgres/migrator.ts`
- Modify: `test/architecture/deployable-roles.test.ts`

- [ ] Write failing architecture tests for queued state, encrypted request, owner/fence/lease, capacity singleton, immutable encrypted frame journal, RLS and least-privilege grants.
- [ ] Run focused tests and confirm schema evidence is absent.
- [ ] Add fresh schema objects and transition guards; do not add backfill or dual-read logic.
- [ ] Grant only exact select/insert/update operations required by the Model Gateway identity.
- [ ] Run architecture tests.

### Task 4: Implement encrypted request/frame persistence

**Files:**
- Modify: `src/modules/model-gateway/infrastructure/crypto/response-protector.ts`
- Create: `src/modules/model-gateway/infrastructure/postgres/model-gateway-stream-repository.ts`
- Modify: `src/modules/model-gateway/infrastructure/postgres/model-gateway-repository.ts`
- Test: `test/unit/model-gateway-response-protector.test.ts`
- Create: `test/unit/model-gateway-stream-repository.test.ts`

- [ ] Write failing tests proving purpose/sequence/digest-bound AAD, no plaintext SQL values, exact sequence chain, capacity rejection, one owner claim and expired owner unknown-only.
- [ ] Run focused tests and observe expected missing APIs.
- [ ] Implement sealed request/frame envelopes, start-or-attach, claim, append/read window, terminal append and expired-owner terminalization.
- [ ] Run focused tests and refactor only after green.

## Chunk 3: Provider dispatcher

### Task 5: Parse and normalize bounded LiteLLM SSE

**Files:**
- Create: `src/modules/model-gateway/infrastructure/http/litellm-sse-parser.ts`
- Modify: `src/modules/model-gateway/infrastructure/http/litellm-chat-adapter.ts`
- Modify: `test/unit/litellm-chat-adapter.test.ts`
- Create: `test/unit/litellm-sse-parser.test.ts`

- [ ] Write failing real-stream tests for fragmented UTF-8 content/reasoning, incremental tool calls, finish and final usage.
- [ ] Add malformed, oversize, timeout, non-2xx, no-usage and retry/fallback-forbidden cases.
- [ ] Implement `stream:true` with one bounded parser and awaited event callback; no provider retry.
- [ ] Run adapter/parser tests.

### Task 6: Add the internal durable dispatcher and coalescer

**Files:**
- Create: `src/modules/model-gateway/application/model-gateway-dispatcher.ts`
- Create: `src/modules/model-gateway/application/model-gateway-frame-coalescer.ts`
- Modify: `src/modules/model-gateway/application/model-gateway-service.ts`
- Create: `test/unit/model-gateway-dispatcher.test.ts`
- Create: `test/unit/model-gateway-frame-coalescer.test.ts`
- Modify: `test/unit/model-gateway-service.test.ts`

- [ ] Write failing tests for 16 KiB/25 ms flush, persistence before publication, client abort isolation, active/queue bounds, same-call attach, one dispatch, hard-timeout unknown and terminal settlement once.
- [ ] Implement start-or-attach, scheduler claim loop, dispatcher-owned AbortControllers and journal tail.
- [ ] Make unary wait on the same terminal journal rather than invoking the provider directly.
- [ ] Run focused application tests.

## Chunk 4: Connect and process lifecycle

### Task 7: Publish StreamModel without leaking internal facts

**Files:**
- Modify: `src/modules/model-gateway/interfaces/connect/model-gateway-connect-service.ts`
- Create: `test/unit/model-gateway-connect-service.test.ts`
- Modify: `src/process/model-gateway-composition.ts`
- Modify: `src/process/model-gateway.ts`
- Modify: process lifecycle tests under `test/architecture/`

- [ ] Write failing Connect tests for first accepted frame, resume cursor, strict order, ResourceExhausted, unary/stream dedupe and caller disconnect stopping only the tail.
- [ ] Map committed journal frames to generated Protobuf and stable Connect codes.
- [ ] Start dispatcher after DB health, stop claims during drain, and abort dispatcher effects only at hard shutdown deadline.
- [ ] Prove database disconnect waits for unknown persistence.

### Task 8: Update local architecture maps and deployment limits

**Files:**
- Modify: `src/modules/model-gateway/INDEX.md`
- Modify: `kokoro-litellm/INDEX.md`
- Modify: `INDEX.md`
- Modify: deployment example environment/manifests as required by composition configuration.

- [ ] Document owner/fence, journal retention/bounds, queue/concurrency, shutdown and no-retry semantics.
- [ ] Ensure no Site/account/secret/provider routing appears in public frames or logs.

## Chunk 5: Verification and atomic commits

### Task 9: Verify Root

- [ ] Run `uv run --locked pytest contract/tests/test_buf_contract.py -q`.
- [ ] Run `pnpm --dir contract run buf:lint`.
- [ ] Run `node scripts/contract/check-boundary-registry.mjs` and focused registry tests.
- [ ] Run `git diff --check`, review generated diff, and commit Root atomically.

### Task 10: Verify Platform

- [ ] Run focused Model Gateway tests after every red-green slice.
- [ ] Run `pnpm typecheck`.
- [ ] Run `pnpm test`.
- [ ] Run `pnpm lint`.
- [ ] Run `pnpm build:runtime`.
- [ ] Run `git diff --check`, review migration/generated files, and commit Platform atomically.
- [ ] Report both hashes and explicitly list Agent `_stream`/`_astream` as the remaining consumer cut.

