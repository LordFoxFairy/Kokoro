# Follow up in a conversation

A follow-up uses the same message operation and session ID as the preceding turn.

1. Wait until the active run is terminal or intentionally steer the active run.
2. Submit the new message to the same session.
3. Generate a new idempotency key for the new logical message.
4. Reopen the session event stream from the last confirmed cursor.

Do not reuse the first message's idempotency key for different content. The same scoped key with different request semantics is a conflict, not a new turn.

If the intent is to modify work already in progress rather than add a later conversation turn, use `run.steer` with a stable `message_id` and non-empty `content`.
