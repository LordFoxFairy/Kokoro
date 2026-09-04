# Request IDs

Every JSON envelope includes `meta.request_id`. The event stream handshake uses `X-Kokoro-Request-Id` because the body is server-sent events rather than JSON.

You may supply an existing correlation value through `x-kokoro-request-id`; otherwise accept the generated value. Record request IDs with operation name, HTTP status, and latency. Keep credentials, full user messages, tool arguments, and provider payloads out of ordinary logs.

A request ID supports diagnosis; it is not an idempotency key, authorization credential, resource ID, or replay cursor.
