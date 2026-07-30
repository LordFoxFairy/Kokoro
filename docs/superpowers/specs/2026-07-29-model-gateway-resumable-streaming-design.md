# Model Gateway Resumable Streaming Design

status: approved
scope: root-contract-platform-provider
owners: team:model-gateway-operations

## Decision

Model Gateway remains one independently deployable Platform process and becomes the sole owner of provider streaming effects.
It exposes a typed Connect server-streaming RPC backed by a PostgreSQL encrypted frame journal. A caller disconnect stops only
that caller's journal tail. It never aborts the provider, changes the invocation owner, releases usage, or creates another effect.

The implementation uses an internal durable dispatcher, not a user-visible Job. A queued invocation can be claimed by any healthy
Gateway instance. Once claimed, its provider effect belongs to that owner/fence. An expired dispatch lease is terminalized as
`outcome_unknown`; another instance must never take over or redispatch that provider effect.

The existing unary `InvokeModel` remains wire compatible. It starts or attaches the same logical invocation and waits on the same
journal. Concurrent unary and streaming calls with the same identity and digest therefore produce one invocation and at most one
provider dispatch.

## Contract

`StreamModel` accepts the complete existing `InvokeModelRequest` plus `after_sequence`. The cursor is the last frame durably
consumed by the caller; zero starts at the beginning. Sequence one is always the persisted `accepted` frame. A resumed tail returns
only frames with a greater sequence and never creates a fresh accepted frame.

Every frame carries:

- opaque invocation and attempt references;
- a strictly increasing positive sequence;
- previous and current SHA-256 frame digests;
- exactly one typed payload: accepted, content delta, reasoning delta, incremental tool call, completed, failed, or
  outcome unknown.

The wire never contains Site, account, authorization-segment, provider account, provider model routing, secret, price, or Hold
facts. Tool-call deltas have a stable zero-based tool index and optional id/name fragments plus a bounded UTF-8 JSON-argument
fragment. Completed frames carry the same safe final projection and usage as the unary response.

Frame digests form a chain over the prior digest, sequence, payload kind, and canonical payload bytes. The first frame uses the
fixed all-zero previous digest. Digests are integrity evidence, not authorization tokens.

## Durable invocation and capacity

Fresh PostgreSQL schema is authoritative; no old-row migration or compatibility reader is added.

An invocation moves through:

```text
queued -> dispatching -> succeeded | failed | outcome_unknown
```

Prepare performs one transaction that:

1. resolves the opaque authorization handle and validates the request digest;
2. locks global dispatch capacity;
3. rejects with `ResourceExhausted` when the bounded waiting queue is full, before Usage prepare or provider I/O;
4. prepares the Credit usage attempt;
5. encrypts and stores the normalized request;
6. inserts the queued invocation and encrypted accepted frame.

The database owns fixed cluster-wide active and queued limits. Claiming locks the singleton capacity row, verifies the queued
state, checks the active limit, moves one invocation to dispatching, increments its owner fence, and records an owner lease before
provider I/O. The queue order is deterministic by accepted time and invocation reference.

The invocation stores last frame sequence, frame count, total plaintext bytes, and last digest. The journal primary key is
`(site_ref, invocation_ref, sequence)`. Database constraints and application validation bound per-frame bytes, total bytes, frame
count, tool indexes, sequence, digest chain, and terminal cardinality. Journal rows are immutable and Site-RLS protected.

Request, delta, and terminal content is AES-256-GCM encrypted before insertion. A frame becomes tail-visible only after its insert
transaction commits. AAD binds purpose, key revision, Site, invocation, request digest, sequence, and frame digest.

## Dispatch and provider stream

The dispatcher is started and stopped with the Model Gateway process. It claims only queued work and reconstructs the prepared
LiteLLM request from the encrypted normalized request. It owns a provider AbortController independent from all Connect request
signals.

Provider events are coalesced with both hard bounds: flush at 16 KiB or 25 ms, whichever occurs first. Each coalesced frame is
encrypted and committed before the dispatcher accepts more provider data, preserving natural backpressure. No token or raw SSE
event opens its own transaction.

LiteLLM receives one OpenAI-compatible request with `stream: true`, retries and fallback disabled, and the stable invocation key.
The bounded SSE parser accepts only UTF-8 `data:` events, `[DONE]`, one choice at index zero, content, `reasoning_content`,
incremental function tool calls, finish reason, and final usage. It bounds headers, line/event/chunk/body sizes, frame count,
aggregate content, tool count, tool argument bytes, and total stream duration. Malformed or ambiguous 2xx streams become
`outcome_unknown`. A complete provider error response becomes a safe `failed` terminal without reflecting provider detail.

There is no provider retry, fallback, hedging, or second attempt in this slice.

## Terminal and recovery semantics

Completed or failed provider truth is finalized in one transaction with Credit usage settlement, local immutable usage fact,
invocation terminal state, encrypted terminal frame, and outbox. Existing settlement business keys and fences make replay
exactly-once.

Provider timeout, process hard-shutdown abort, malformed/ambiguous stream, or expired dispatch owner is finalized as durable
`outcome_unknown` with the existing Credit unknown fence. It is never permission to redispatch. Trusted reconciliation may later
finalize the same unknown invocation and append one terminal correction, but it cannot invoke a provider.

Graceful shutdown stops new claims and new RPC admission, drains tails and active provider streams to a deadline, then aborts only
dispatcher-owned provider controllers. Each aborted dispatch must persist `outcome_unknown` before database disconnect is accepted.

## Tail and unary compatibility

Tails poll or notify only committed journal rows. A client signal stops that AsyncIterator and releases no invocation state. A
cursor beyond the durable high watermark, a digest/sequence discontinuity, or an expired/unavailable journal is a typed failure and
never triggers provider work.

Unary `InvokeModel` uses start-or-attach and tails to a terminal frame. It projects the existing `InvokeModelResponse` exactly;
disconnecting the unary wait does not stop dispatch. The future Agent `_stream`/`_astream` adapter will consume `StreamModel`, but
Agent code and GA graph/checkpoint/handoff/terminal semantics are intentionally outside this change.

## Verification

- Root Proto/Buf validation and machine registry tests cover method shape, cursor, payload closure, digest fields, bounds, and
  same-identity receipt semantics.
- Platform unit tests cover capacity rejection before Usage/provider, one claim across instances, expired-owner unknown,
  disconnect-only-tail, coalescing, encryption-before-visibility, digest/sequence/size limits, terminal settlement once, unary plus
  stream dedupe, and no retry/fallback.
- LiteLLM adapter tests use real bounded ReadableStream fixtures for fragmented UTF-8 SSE, reasoning, incremental tools, final
  usage, malformed/oversize streams, timeout, and provider error.
- Repository and migration tests prove RLS, immutable frames, owner/fence transitions, grants, and fresh-only schema.
- Full Platform lint, typecheck, unit suite, runtime build, and Root contract gates run before commits.

