# UTC and RFC 3339 time

API instants use RFC 3339 UTC, normally with millisecond precision:

```text
2026-09-04T12:34:56.123Z
```

Parse them as timezone-aware instants. Preserve the original instant for ordering and convert only for display. Do not store a timezone-free local timestamp or use numeric seconds where the schema requires `date-time`.

Scheduled tasks additionally carry local `time` and an IANA `timezone`. Keep both for recurring intent, and use `next_run_at` as the concrete upcoming UTC occurrence.

The current Project instruction revision model has documented compatibility fields that use different naming/time representation. Follow its generated schema until the owner contract changes; do not claim those fields are already RFC 3339.
