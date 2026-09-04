# Upload project resources

The current v1 operation accepts multipart files and requires an idempotency key.

<<< ../../examples/curl/upload-resource.sh{bash}

## Current observable behavior

The success response is the generic `{ "data": { "ok": true }, "meta": { "request_id": "..." } }` envelope. It confirms BFF acceptance only.

Version 1.0.0 does **not** publish a resource ID, upload session, scan state, processing status, or resource-specific polling endpoint. Therefore:

- retain the source file and request ID until your product workflow confirms the intended outcome;
- do not claim that a virus scan or asynchronous promotion completed from `ok: true`;
- do not poll an internal Storage endpoint or infer an object key;
- use the public Library projection only for items it actually returns.

A complete resource lifecycle will require an additive or versioned BFF contract change before this guide can describe polling or promotion.
