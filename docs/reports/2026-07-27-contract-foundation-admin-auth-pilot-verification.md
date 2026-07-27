# Contract Foundation / Admin Auth Connect Pilot Verification

状态：通过（2026-07-27）

## Candidate pins

| Repository | Commit | Recoverable ref |
| --- | --- | --- |
| `kokoro-agent` | `c2a92c85dcf68e5fe0da9fd5bba84131c9d9e537` | `kokoro-wave1-federated-ci-2026-07-27-agent` |
| `kokoro-platform` | `0463513cb9dc04a9fe7fea4f06f098fc1f890845` | `kokoro-admin-auth-connect-2026-07-27-platform` |
| `kokoro-session` | `ffc9b39c993d4272f6d115de411a133ea1290a70` | `kokoro-platform-admission-boundary-2026-07-27-session` |
| `kokoro-web` | `da320354262befea51e9d868def8bcd8532a1762` | `kokoro-admin-auth-connect-2026-07-27-web` |

## Implemented facts

- Root owns Admin Auth v1 Proto/Buf source, exact tool versions, generated mirror checks and live compatibility orchestration.
- Platform Admin is the only owner/writer for operator lookup, verification-token effects, auth events and command receipts.
- Admin Web consumes a server-only generated Connect client and has no Platform Prisma schema, Prisma dependency or database credential.
- Effect requests embed method-specific protobuf Effect messages. Root generation emits one byte-identical Node digest helper to Platform and Web.
- Command identity and receipts persist the explicit `SHA256_PROTOBUF_V1` algorithm. The digest is lowercase SHA-256 over domain-separated, normalized, known-field protobuf bytes; unknown fields are discarded.
- Proto auth/indexed string bounds match the Platform MySQL `VARCHAR(191)` owner schema.
- Platform RPC telemetry exposes bounded Prometheus labels and fail-open, fixed-field security audit records without request payloads, credentials, email, command IDs or digests.
- Session exposes one transport-independent `PlatformAdmissionPort`; Prepare and Finalize receipts have separate discriminators and Finalize can express `committed`. GA source is unchanged.

- Contract source digest: `49fbec7964214d82ce189e479b014edc846d7cd0d1ef1facd355b0a80fea6293`
- Generated artifact digest: `e4c0f68e5891c9f83a26b8a6c74552931f5d6d6c559c3d35a036aa3e53f90267`

## Verification evidence

Root candidate:

```text
generated mirror check: pass
legacy contract mirror check: 19/19
contract policy tests: 35/35
repository + compatibility tests: 68/68
remote recoverable-ref / proposed-index verification: pass (4 repositories)
```

Child repositories:

```text
Platform full unit matrix: 1,082 tests passed after digest migration
Platform typecheck/lint: pass
Platform Admin fresh MySQL migrate deploy: 6 migrations applied
Platform Admin real Connect + Prisma integration: 12/12
Web Admin tests: 41/41
Web Admin typecheck/lint/Next production build: pass
Session tests: 372 passed, 27 skipped integration tests; typecheck/lint: pass
GA tracked diff: empty
```

Root pinned runtime compatibility:

```text
outcome: pass
combination digest: 3f53cf566acfdb03eced966de9d386f9a2d6be94d4d86bf40015b992fff7b4f8
preflight pin verification: pass
postflight pin verification: pass
mysql / redis / mongo / minio / litellm: healthy
web-session-http-sse: pass
session-platform-internal-rpc: pass
session-agent-durable-localfake: pass
agent-model-gateway-localfake: pass
platform-admin-auth-connect: pass (11 closed assertions)
```

The machine evidence is retained under ignored `tmp/admin-auth-compatibility.json`; it contains only the closed evidence schema.

## Cleanup and observations

- The isolated database lease, databases and test users were cleaned by the Root runner.
- All five `kokoro-infra` verification containers were stopped and removed after the gate. Named CI volumes and images were retained; no dev volume was deleted.
- One initial Session full-suite run observed a transient `DELETE /sessions/ghost` 404. The focused case then passed 20/20 consecutive isolated runs and the subsequent full suite passed. No code change was made without a reproducible root cause.
- This pilot establishes the Session application boundary only. The real Platform Admission provider/generated client and timeout-after-commit cross-service reconciliation remain a later Admission RPC wave; the legacy adapter does not claim that remote behavior today.
