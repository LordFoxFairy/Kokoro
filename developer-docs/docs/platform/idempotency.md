# Idempotency

The generated reference marks each operation as `required` or `none` through canonical metadata. Mutations marked `required` need `Idempotency-Key`; reads and the explicit GitHub preview operation do not.

## Key lifecycle

1. Create a key before the first attempt.
2. Persist the key with the exact request semantics.
3. Reuse both after timeout, disconnect, or a retryable response.
4. Retire the key when the result is known; never recycle it for unrelated work.

`idempotency_conflict` means the key was reused for different semantics. `idempotency_in_progress` means another attempt still owns the pending claim; back off with jitter and retry the identical command.

Idempotency prevents duplicate admission. It does not make downstream UI reduction, file handling, or webhook processing automatically idempotent; those consumers still need stable resource and event identities.
