# AG-UI stream and replay

Kokoro uses AG-UI over server-sent events for Agent progress. The public stream is a BFF projection: internal Agent facts and provider payloads are not public cursor or event contracts.

## Frame shape

Each event has an SSE `id` and one JSON `data` value. The `id` is an opaque `agui_*` cursor assigned to that individual public frame. A single source fact may expand into multiple public frames, each with its own cursor.

Common AG-UI event families include run start/finish/error, text message start/content/end, tool call start/arguments/end/result, activity, subagent, and explicitly named custom product events. Clients should validate the `type` before reducing a frame into UI state.

## Replay rule

1. Read a complete frame.
2. Persist its exact `id` in the session's scope.
3. Apply the frame idempotently to client state.
4. After disconnect, reconnect with `Last-Event-ID: <saved id>`.

The server resumes strictly after that frame. Never parse, increment, synthesize, or reuse the cursor for another session or namespace. Invalid, unknown, or foreign-scope cursors return `invalid_event_cursor`.

## Delivery semantics

Reconnects can replay data around a client-side failure boundary. Reducers should identify messages, runs, and tool calls by their stable IDs and tolerate a repeated frame. A keep-alive comment carries no application event and should not advance the saved cursor.

The current beta ledger has no published cursor-expiry behavior because retention and GC are not yet part of v1's observable contract.
