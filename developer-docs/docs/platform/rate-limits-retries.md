# Rate limits and retries

Kokoro v1 does not currently publish a numeric client quota or standard rate-limit response-header schema. A `429` response means the caller must slow down; do not infer a quota from observed traffic.

## Retry policy

| Situation | Client behavior |
| --- | --- |
| Safe read receives a transient `5xx` | Retry inside a bounded timeout with exponential backoff and jitter |
| Mutation response is uncertain | Retry the identical request with the same idempotency key |
| `idempotency_in_progress` | Back off, then retry the same command |
| `idempotency_conflict` | Stop and fix key/request reuse |
| `429` | Honor `Retry-After` when present; otherwise use bounded exponential backoff |
| Validation, auth, or not-found `4xx` | Fix the request or permissions; do not loop |

Cap attempts and total elapsed time. Propagate cancellation from the original caller. Opening parallel retries with different idempotency keys can duplicate work and defeats the command contract.
