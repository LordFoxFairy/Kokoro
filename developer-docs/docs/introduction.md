# Introduction

Kokoro API v1 is the public Product API contract owned by `kokoro-bff`. It exposes projects, chat sessions, asynchronous Agent runs, scheduled tasks, library projections, and supporting product resources through one versioned HTTP surface.

The portal composes guides and generated reference material. It does not own or copy the API schema. Every reference page is generated from the pinned canonical OpenAPI artifact in the BFF repository.

## Current contract status

Version `1.0.0` is marked **beta**. An operation appearing in the contract describes its public wire shape; it does not by itself prove that every live adapter, persistence path, or service-level objective is complete.

## Request model

Kokoro uses an asynchronous command model for Agent work:

1. Submit a message with an `Idempotency-Key`.
2. Receive `202 Accepted` with stable run and message identifiers.
3. Follow the AG-UI server-sent event stream.
4. Persist each opaque SSE `id` and reuse it as `Last-Event-ID` after a disconnect.
5. Treat `RUN_FINISHED` or `RUN_ERROR` as the stream terminal signal.

JSON responses use a stable success or error envelope and always carry a request ID. Time instants are RFC 3339 UTC strings unless the generated reference identifies a documented compatibility exception.

## Ownership boundary

This portal publishes only operations whose canonical metadata says `x-kokoro-owner: kokoro-bff` and `x-kokoro-visibility: public`. Internal owner APIs, storage schemas, provider payloads, and generated internal DTOs are not publication inputs.

Continue with the [quickstart](./quickstart) or inspect the [v1 reference](./reference/v1/).
