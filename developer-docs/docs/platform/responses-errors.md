# Response and error envelopes

JSON success responses use:

```json
{
  "data": {},
  "meta": { "request_id": "req_example" }
}
```

JSON errors use:

```json
{
  "error": {
    "code": "stable_error_code",
    "message": "Log-safe message"
  },
  "meta": { "request_id": "req_example" }
}
```

Program against `error.code`, HTTP status, and the operation's generated response schema. Treat `message` as diagnostic text, not a stable localization key. Optional error details must be validated before use.

The AG-UI SSE operation is not wrapped in a JSON success envelope. Its stream handshake exposes the request ID in `X-Kokoro-Request-Id`, and each data frame follows the AG-UI event shape.
