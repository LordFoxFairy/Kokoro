# Federated compatibility scenarios

Root owns scenario orchestration and the closed FD3 machine-result envelope. Each scenario starts
the exact checked-out provider, invokes an official consumer-owned command, uses only lease-scoped
Infra data, and terminates its complete process group. Scenario stdout/stderr is never evidence and
must not contain credentials or payloads.

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
