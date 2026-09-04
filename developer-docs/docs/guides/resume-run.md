# Resume a waiting run

Resume only after the public projection indicates a pending interaction and your application has collected every required decision.

Send a `run.resume` control body with a non-empty `decisions` array. Decision objects are interaction-specific; preserve the identifiers supplied by the public event or session projection and do not invent internal tool references.

The checked TypeScript example submits an approval decision, then reconnects to the stream:

<<< ../../examples/typescript/run-lifecycle.ts{ts}

Reuse the same idempotency key when retrying this decision set. Changing a decision requires a new logical command and key, subject to the run still accepting input.
