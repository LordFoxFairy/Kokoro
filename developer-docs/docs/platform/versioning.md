# Versioning and deprecation

The current contract version is `1.0.0` on the `/v1` namespace and its operations are marked beta.

## Compatibility policy

Additive optional fields, new error codes, and new operations may remain in v1 when schema, examples, and tests change together. Removing a path or method, renaming an operation ID, making optional input required, narrowing a response, or changing permission or idempotency semantics requires a new API version.

Clients should ignore unknown response fields after schema validation, avoid exhaustive assumptions about additive error codes, and pin the contract version used to generate their integration.

The v1 contract does not currently define a `Sunset` header or a public deprecation schedule. Deprecation details will appear in the canonical owner contract and [changelog](../changelog) before a published retirement.
