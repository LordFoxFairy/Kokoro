# Lifecycle and status

Kokoro exposes related, but distinct, status machines. Do not collapse them into one client enum.

## Run status

```text
running ── interaction required ──> waiting
   │                                  │
   │                                  └─ resume ─> running
   ├─ cancel ─> cancelled
   ├─ success ─> completed
   └─ failure ─> failed
```

The current `ChatRun` schema exposes `running`, `waiting`, `completed`, `cancelled`, and `failed`. The initial `202` receipt represents admission before a later snapshot or event confirms the state.

## Message status

Assistant messages can move from `pending` to `streaming`, then to `completed` or `failed`. Render partial content as provisional until its message-end or terminal frame is committed.

## Control receipt status

A control command has its own `pending`, `succeeded`, or `failed` receipt. This describes command processing, not the entire Agent run.

## Scheduled task status

Scheduled tasks expose `active`, `paused`, or `failed`, plus a separate `enabled` flag and optional expiry. A task lifecycle must not be inferred from a run launched by one occurrence.
