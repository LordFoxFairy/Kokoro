# Task A C-1.3 profile-read cutover evidence (2026-10-31)

## Scope and design decision

The profile read is an IAM-owned projection, not an OAuth userinfo relay. The fixed chain is:

```text
App GET /api/account/profile
  → admittedProductSession (native Cookie + fixed Origin; legacy Product Session only during transition)
  → BFF GET /v1/account/profile
  → IAM GET /internal/v1/account/profile
  → subject-bound { subject, name, email, email_verified }
  → App final admission re-check
```

The request is bodyless and queryless. BFF materializes only the allowlisted IAM Cookie, configured Origin, request id and direct `session_admission` credential for native requests. Legacy bearer remains only as an explicit transitional consumer. Every hop requires `no-store`, matching `x-request-id`, JSON content type, no `Location`/`Set-Cookie`, bounded body bytes, cancellation and one absolute deadline. No BFF database read, receipt, generic DTO or second network protocol was introduced.

## Pinned commits

| Owner | Commit | Deliverable |
|---|---|---|
| IAM | `497900ab6ec7274c800f1889cc06c993662dd9d6` | `GET /internal/v1/account/profile`, OpenAPI artifact, native/bearer guard, repository/service projection, contract/unit/integration tests |
| BFF | `091cd50` | vendored IAM artifact and generated client, public `GET /v1/account/profile`, native owner transport, strict error/response mapping and HTTP tests |
| App | `da82d2a9` | App profile read through BFF, native/legacy admission seam, subject binding, final re-admission, focused and integration tests |
| Root | `c7af342b` | exact submodule gitlinks for the three consumers |

## Verification actually run

- IAM: `pnpm typecheck`; `pnpm contract:check`; `pnpm format:check`; `pnpm lint`; focused Vitest: 5 files / 64 tests passed. Real integration command was attempted and stopped before test execution because `IAM_TEST_ADMIN_URL is required for real infrastructure tests`.
- BFF: `pnpm build`; `pnpm lint`; `pnpm typecheck`; `pnpm contract:check:iam`; profile input/client/http/contract tests: 49 passed. IAM client generation is deterministic and pinned to owner commit/digest.
- App: BFF account-profile client generation check passed (16 files); profile App/integration/update/contract tests: 62 passed; `pnpm lint` passed. Full App typecheck still has the pre-existing `app-frame-main-surface.tsx:onReconnect` error, recorded as `TA-BASELINE-01`.
- Root: submodule gitlinks are pinned in `c7af342b`; no A-01/A-02/A-07 files were touched.

## Open evidence and next gate

The implementation gate is closed for code/artifacts/focused behavior, but C-1.3 remains **in progress** until a real IAM infrastructure receipt covers native Cookie, fixed Origin, tenant/subject binding, permission and revocation. The environment gap is explicit and does not count as a pass. Once the receipt is available, update `TA-C1.3-05`, then start the first C-2 slice: migrate the existing `PERSONALIZATION_PROVIDER` `GET/PUT /v1/preferences/personalization` route with a red HTTP/architecture test before touching unrelated LegacyRoutes or global repositories.
