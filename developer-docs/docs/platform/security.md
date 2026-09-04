# Security

## Keep the service boundary server-side

Call Kokoro from a trusted backend or same-origin server adapter. Never expose the service credential, trusted namespace, or principal headers to browser code. Browser-supplied host, forwarded, tenant, or identity values are untrusted input.

## Minimize data exposure

- Send only fields declared by the public request schema.
- Do not log credentials, full user content, tool arguments, or artifact payloads by default.
- Treat share IDs, cursors, resource IDs, and URLs as opaque; none substitutes for authorization.
- Validate response envelopes and AG-UI event types before use.
- Enforce request timeout, cancellation, response-size, and upload-size budgets in the calling server.

## Isolate by trusted context

Namespace and principal come from authenticated server state. Keep pagination and replay cursors scoped to that context and resource. A cursor from another tenant or session must be rejected without probing whether the foreign resource exists.

## Report safely

Capture the public operation ID, HTTP status, and request ID when investigating. Do not attach a deployed credential or unredacted user payload to an issue or support request.
