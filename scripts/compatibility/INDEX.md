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
| `web-session-http-sse.mjs` | Session | Web | HTTP snapshot + resumable SSE |
| `session-platform-internal-rpc.mjs` | Platform | Session | Legacy Platform runtime characterization |
| `session_agent_durable.py` | Agent | Session | Durable command/fact transport |
| `agent_model_gateway.py` | Platform | Agent | Model gateway HTTP |
| `admin-auth-connect.mjs` | Platform | Admin Web | Generated ConnectRPC `AdminAuthService.v1` |

The Admin Auth scenario runs Platform's official migration and seed commands, starts the real
Fastify provider, and invokes Web's `compat:admin-auth` command. The consumer command owns protocol
assertions; Root owns isolation, timeout, cleanup, digest attestation, and the single machine result.

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
