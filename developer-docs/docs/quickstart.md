# Quickstart

Submit an Agent message from a trusted server, capture the run receipt, and then follow its AG-UI stream.

## 1. Configure a local environment

The examples intentionally require environment variables so credentials never appear in source. Use values issued for your deployment; the values below are non-secret local placeholders.

```bash
export KOKORO_API_BASE_URL="http://127.0.0.1:4300"
export KOKORO_API_TOKEN="example-only-token"
export KOKORO_NAMESPACE="ns_example"
export KOKORO_PRINCIPAL_ID="principal_example"
export KOKORO_SESSION_ID="session_example"
```

::: warning Server-side only
The service token and trusted identity context belong in a server adapter or backend. Do not place them in browser JavaScript, mobile bundles, URLs, or logs.
:::

## 2. Submit the message

This checked-in cURL program is executed against a credential-free fixture by `pnpm examples:check`.

<<< ../examples/curl/create-run.sh{bash}

The response is `202 Accepted`. `data.run_id` identifies the asynchronous run; acceptance is not completion.

## 3. Follow and resume

Open `GET /v1/sessions/{id}/events` with `Accept: text/event-stream`. Persist every SSE `id` exactly as received. On reconnect, send that value in `Last-Event-ID`; do not decode it or substitute an Agent sequence.

The complete [TypeScript lifecycle example](./guides/replay-after-disconnect) demonstrates initial streaming, resume control, and cursor-based replay.

## 4. Correlate failures

Store `meta.request_id` from JSON responses. For the stream handshake, capture `X-Kokoro-Request-Id`. Include the ID when investigating a failed request, but never log service credentials or user payloads by default.
