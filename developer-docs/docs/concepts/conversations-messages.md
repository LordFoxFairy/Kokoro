# Conversations and messages

The v1 wire name for a conversation is **session**. A session snapshot contains the conversation metadata, a bounded message projection, the active run, pending pauses, files, deliveries, and the current event watermark.

## Messages are asynchronous commands

`POST /v1/sessions/{id}/messages` admits a user message and returns a receipt. The receipt contains `run_id`, `user_message_id`, and `assistant_message_id`; it does not contain a completed answer.

Message status values are `pending`, `streaming`, `completed`, and `failed`. Full history uses the separate cursor-paginated messages operation rather than an unbounded session snapshot.

## Follow-up behavior

Submit a later message to the same session ID to continue the conversation. Give each new logical message a new idempotency key. When retrying that same message after an uncertain response, reuse its original key and identical request semantics.

## Current beta boundary

The public wire contract and durable AG-UI projection are BFF-owned. Current live Conversation, Message, and Share product-fact ownership is still being closed; contract availability alone is not an uptime or persistence claim.
