# Scheduled tasks

A scheduled task is a BFF product resource that describes recurring work. The public model includes a title, prompt, daily or weekly frequency, local time, IANA timezone string, next run instant, optional expiry, approval behavior, enabled flag, and status.

## Time model

`time` and `timezone` preserve the intended local schedule. `next_run_at` is the concrete RFC 3339 UTC instant clients should display and monitor. Do not replace an IANA timezone with a fixed UTC offset; daylight-saving transitions require the named location.

## Commands

Create, update, delete, and retry operations require an `Idempotency-Key`. A project-scoped create operation takes the project identity from the URL path. The caller must not attempt to override it in the body.

The public BFF resource is distinct from internal scheduler leases, occurrences, and dispatch commands. Those internal protocols are not part of this portal.
