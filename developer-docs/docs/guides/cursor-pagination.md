# Cursor pagination

List operations that publish pagination return an opaque `next_cursor`. Send it back unchanged with the next request and keep the other filters stable.

<<< ../../examples/python/cursor-pagination.py{py}

## Rules

- Respect the operation's documented `limit`; session lists accept 1 through 100.
- Treat `null` or an omitted optional next cursor as the end.
- Do not decode a cursor, convert it to an offset, or use it with a different filter set.
- Restart from the first page when the server rejects a stale or invalid cursor.

Pagination cursors and AG-UI replay cursors are different token types and are never interchangeable.
