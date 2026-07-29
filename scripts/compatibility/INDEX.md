---
architectureIndex: 1
rootId: root.scripts.compatibility
owners:
  - "@LordFoxFairy"
---

# Federated compatibility scenarios

## Responsibilities

Own Root orchestration for exact-pin provider/consumer scenarios and the closed FD3 machine-result envelope.

## Non-responsibilities

Scenarios do not replace child tests, mutate product data, or inspect private service tables.

## Public boundary

| Scenario | Provider | Consumer | Boundary |
|---|---|---|---|
| `web-session-http-sse.mjs` | Session | Web | Host-bound Site resolution + authenticated HTTP snapshot + resumable SSE |
| `session-platform-internal-rpc.mjs` | Platform | Session | Legacy Platform runtime characterization |
| `session_agent_durable.py` | Agent | Session | Durable command/fact transport |
| `agent_model_gateway.py` | Platform | Agent | Model gateway HTTP |
| `admin-auth-connect.mjs` | Platform | Admin Web | Generated ConnectRPC `AdminAuthService.v1` + `AdminCommandService.v2` |
| `hub-runtime.mjs` | Platform Hub | Session + Agent | Capability resolve + secret resolve HTTP |

The Admin control scenario runs Platform's official migration and seed commands, starts the real
Fastify provider, and invokes Web's `compat:admin-auth` command. The consumer/provider probe set owns protocol
assertions; Root owns isolation, timeout, cleanup, digest attestation, and the single machine result. V2 evidence
is closed over mTLS binding, exact command digest and operator attestation axes, maker/checker independence,
checker-only queueing, Worker-only execution, frozen authority epochs, atomic terminalization, stale-authority
no-effect, receipt recovery, break-glass review, and proof that the retired client execution authority is unreachable.

The Hub runtime scenario starts the real Hub against the lease-scoped Mongo database and an HTTP membership
fixture that validates Hub's own caller credential. It creates the test secret only through the public self
API, then invokes Session and Agent's child-owned compatibility commands, which wrap their production clients.
Root never imports sibling runtime source or seeds a private Hub collection.

The Web/Session scenario's closed local HTTP fixture exposes only the production-shaped
`/site-context/resolve` and `/hub/runtime/resolve` reads. Web runs with strict Host resolution and no development
fallback; unknown Hosts, callers, namespaces, methods, and paths fail closed. Readiness reports phase/status-only
reason codes, drains rejected probe bodies, and aborts immediately when a child exits. Fixture routes accept one
exact query key with cardinality one. The SSE handshake and reads are bounded; its parser consumes only
blank-line-terminated frames and retains an incomplete tail across chunks.

## Callers and dependencies

`run-pinned-compatibility.mjs` invokes scenarios by code-owned ID against exact checked-out providers and official consumer commands.

## Data ownership and events

Scenarios own only lease-scoped test data and sanitized machine results; child services own all runtime records and event streams.

## Runtime and security

Each scenario uses Root Infra, bounded timeouts, complete process-group cleanup, and no credentials or payloads in stdout/stderr evidence.

## Idempotency, failure, and recovery

Repeated runs use isolated scopes. Missing dependencies, malformed results, timeouts, or required skips fail the combination gate.

## Extension rules and forbidden dependencies

Add commands to the closed code-owned registry. Never accept arbitrary manifest argv, use child Compose, or cross a private database boundary.

## Current gotchas

The legacy Session/Platform characterization is not proof that generated Admission RPC has been implemented.

## Verification

Run `node --test scripts/compatibility/*.test.mjs` and `uv run pytest scripts/compatibility -q` before the full pinned runner.
