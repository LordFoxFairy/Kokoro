# Build idempotent commands

Generate an unpredictable, stable key for each logical mutation. Store it beside the local command until the outcome is known.

## Retry contract

- Same key + same namespace + same method + same canonical path + same request semantics: replay the original result.
- Same scoped key + different semantics: `idempotency_conflict`.
- The first request is still active: `idempotency_in_progress`.
- A transport failure or retryable server failure: retry with the same key and unchanged request.

Do not put timestamps or attempt counters into a retried body. They change request semantics and can turn recovery into a conflict.

## Current beta note

The deployed implementation's fingerprint currently normalizes the body but has not yet closed query and selected-header coverage across every path. Callers should still keep the entire method, URL, query, selected headers, and body stable; this is the intended public behavior and avoids depending on a temporary implementation gap.
