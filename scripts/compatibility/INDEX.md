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
| `hub-runtime.mjs` | Platform Hub | Agent | Signed execution assembly resolve + streamed Skill artifact over ConnectRPC |

The Hub runtime scenario starts the real Hub HTTP and ConnectRPC providers against the lease-scoped Mongo
database, uploads a Skill through the official Admin API, and freezes the signed catalog through the real
Platform projection handler. It then invokes Agent's production Hub client to resolve the exact execution
assembly and stream the referenced artifact, verifies the artifact digest, and proves a Platform identity
cannot call the Agent-only runtime. Root never seeds a private Hub collection.

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
