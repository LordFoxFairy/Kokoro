# Replay after disconnect

Persist the last fully received SSE `id` before acknowledging the corresponding UI state. Reconnect to the same session with that exact value in `Last-Event-ID`.

<<< ../../examples/typescript/run-lifecycle.ts{ts}

## Recovery checklist

- Scope a saved cursor by trusted namespace and session ID.
- Do not parse the `agui_*` value or replace it with `metadata.kokoro.seq`.
- Rebuild state with stable run, message, tool, and delivery identifiers.
- Ignore SSE comments when advancing the cursor.
- Stop only on a terminal event or an explicit user action; a dropped socket is not completion.

If the server returns `invalid_event_cursor`, discard only the rejected cursor and refresh the authorized session snapshot. Do not probe cursors from another scope.
