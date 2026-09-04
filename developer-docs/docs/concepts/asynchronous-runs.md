# Asynchronous Agent runs

An Agent run begins when the message operation returns `202 Accepted`. Keep the returned `run_id`; use it with the session ID for control commands and use the session event stream for progress.

## Why admission is separate

Model and tool work can outlive an HTTP request. The receipt confirms admission and stable identities, while AG-UI frames communicate progress and completion. This separation makes retries and reconnects explicit.

## Control commands

The run control operation accepts a discriminated request:

- `run.cancel` asks the active run to stop.
- `run.resume` supplies one or more decisions for a waiting interaction.
- `run.steer` adds a message ID and new instruction to steer work.

Every control request is idempotent and returns a control receipt with `pending`, `succeeded`, or `failed` status. A pending control receipt is not the run's terminal status.

## Terminal observation

Use the event stream as the progress channel. `RUN_FINISHED` indicates successful stream completion and `RUN_ERROR` indicates failure. A transport disconnect is not a run outcome; reconnect using the last confirmed cursor.
