# Authentication and service context

Kokoro API v1 is a server-to-server Product API. A trusted server adapter supplies service identity, credential, namespace, and principal context. Browser code must not hold service credentials or call the BFF directly.

The executable examples use conspicuously fake environment values and a local fixture server. Never commit or embed a deployed credential in documentation, client bundles, logs, or source control.

## Required context

Except for health and readiness probes, the v1 contract declares four service-context schemes:

| Header | Purpose | Source |
| --- | --- | --- |
| `x-kokoro-service` | Identifies the admitted server caller | Deployment configuration |
| `x-kokoro-internal-secret` | Authenticates that caller | Secret manager |
| `x-kokoro-namespace` | Selects the trusted product scope | Sealed server session |
| `x-kokoro-principal-id` | Identifies the trusted principal | Sealed server session |

An optional `x-kokoro-request-id` may carry an existing correlation ID. If it is absent, the service still returns a request ID in the response envelope.

## Trust rules

- Derive namespace and principal on the server; do not accept them as browser authority.
- Do not forward browser-supplied tenant, `Host`, `X-Domain`, or `X-Forwarded-*` values as trusted identity.
- A share identifier selects a shared resource; it is not a replacement for server service authentication.
- The `scope` query parameter is only a filter and cannot override authenticated identity.

## Credential handling

Load service credentials at process start from the deployment secret mechanism. Redact all four context headers from logs and traces. Rotate a credential through deployment configuration rather than distributing it in examples or SDK defaults.
