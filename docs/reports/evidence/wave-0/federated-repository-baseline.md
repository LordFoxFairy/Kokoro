# Wave 0 Federated Repository Baseline

Baseline executed: `2026-07-27T04:09:33Z`
Source freeze regenerated: `2026-07-27T04:29:17Z`
Root freeze parent: `26c4e4e8165a154d01be8c1d34e90e0debb1c9f4`
Scope: exact independent-repository lock/gitlink baseline before root compatibility and pin-promotion governance.

This report records observed results; red gates are not rewritten as green. No production credentials or user data were used.
Redis, MongoDB, MySQL, and MinIO integration checks initially used four ad-hoc disposable containers bound to `127.0.0.1` on
ports 16379, 27018, 13307, and 19100 with test-only credentials. This exposed an execution-design defect: Kokoro already has a
root-managed Infra authority, so creating a second unmanaged stack is not an acceptable repeatable verification path. All four
temporary containers and the previously running local Kokoro containers were removed after the owner requested resource cleanup;
Docker volumes and images were not removed. Subsequent Wave 0 automation must use the root Infra lifecycle and logical test
database/key/bucket isolation instead of parallel ad-hoc infrastructure.

## Toolchain actually used

| Tool | Observed version |
|---|---|
| Git | `2.39.5 (Apple Git-154)` |
| Node.js | `22.22.2` |
| pnpm | `11.2.2` |
| uv | `0.9.4` |
| Agent Python | `3.11.14` |
| Docker Engine | `28.5.1` |

These are the old-environment baseline tools, not the Wave 0 target versions.

## Infra authority diagnostic

After cleanup, `docker ps` and `docker ps -a` both reported zero containers. Read-only Docker inventory reported 27 images
(40.58 GB), 59 local volumes (10.29 GB), and 157 build-cache records (21.11 GB). Nothing was pruned.

The inventory proves that earlier entry-point drift created multiple physical volume families:

- `kokoro-infra_kokoro-{mysql,redis,mongo,minio}` from project `kokoro-infra`;
- `kokoro_kokoro-{mysql,redis,mongo,minio}` from project `kokoro`;
- older `kokoro_dev_{mysql,redis,mongo}_data` and `kokoro-platform_kokoro-platform-mysql`;
- `kokoro_kokoro-workspace` plus the independent Langfuse data volumes.

The two four-volume families were created on 2026-07-19 under different Compose project labels even though the compose file claims
one Infra stack. The root compose example used project `kokoro`, while provision/dev orchestration used `kokoro-infra`. Volume names
alone do not prove which family holds authoritative data. Wave 0 therefore fixes the authority and prevents new duplicates, but does
not delete or adopt an existing volume until an inventory, backup and restore test identifies the correct source and the owner approves
the exact destructive target.

## Exact source freeze

```bash
node scripts/repository/freeze-snapshots.mjs \
  --approved-spec-commit 31ed730a41ec79130ca530d6acbd3f3d9b445485 \
  --expected config/repository/expected-snapshots.json
```

produced [the machine-readable manifest](../../../../config/repository/frozen-submodules.yaml). All four pin/tree/archive/file-count
values match the approved baseline. The four recovery tags and bundles were subsequently created and restore-tested; the current
manifest records every remote archive ref as reachable. The repositories remain independent submodules by owner decision.

| Source | Pin | Tree | Archive SHA-256 | Files | Remote main at capture | Result |
|---|---|---|---|---:|---|---|
| Agent | `18b394dc3df019244875e643c142c2b08b9db708` | `b06557b5876125f2a014bc6b9597bb7ac9a30780` | `670927a78d57bef29a4a11ff6782960ae117cc526b0c88af3a234154c0f78340` | 150 | same pin | frozen |
| Platform | `d30a16a782aca0fe131acbe8cbfbbd63fdf1b989` | `4093ce419d57089b5128ff1783a41fc6bc1733b8` | `d43330451610cfea414e9256dc640a09be2fcd727446ed99f01b000c885392c5` | 525 | `9c81c413d054f858436fb781ad24692b14981746` | local pin ahead; Task 2 anchor required |
| Session | `4f4aa3defc5cce79be58c447d7f053c6204ef48f` | `55ea2b5d6c50eb172e5eb1cedf6b09f7b7526bca` | `32d8d5fd8db3cdae8a03e6d375cb66483be67abaf0ebe7da9cab438518218d7a` | 97 | same pin | frozen |
| Web | `f3936befb7ae4c219273ae9b7f4efb97cb6a1425` | `c88c4f29197fafb1158c561e1bfe8153d04e7fcc` | `202b99d74fd2720298d78df95b18f3372adf2f11c1a2751f712e8a84f0a9d047` | 329 | `5a3a0c4cb72ba80ba19dd335824e504119f7ef4b` | local pin ahead; Task 2 anchor required |

## Contract

| Command | Result |
|---|---|
| `python3 contract/check.py` | PASS — 17 generated mirrors match |
| `python3 -m pytest contract/tests -q` | PASS — 23 tests |

## Agent — Python 3.11 and old `uv.lock`

Environment was created with `uv sync --python 3.11 --locked`. Tests used the disposable Redis/Mongo/MinIO endpoints and
explicit test-only MinIO credentials, preventing the test helper from reading any ignored env file.

| Command | Result |
|---|---|
| `uv run --python 3.11 --locked pytest -q` | PASS — 609 passed; 4 warnings |
| `uv run --python 3.11 --locked ruff check .` | FAIL — 16 findings: 3 unused `SKIP_REASON` imports and 13 import-order findings |
| `uv run --python 3.11 --locked pyright` | FAIL — the same 3 unused imports |

The pytest warnings are two LangChain beta-stream warnings and two WebSocket deprecations. The deterministic GA runtime corpus is
captured while this pinned Agent lock remains available. Agent keeps its independent Python lock and release line; a future runtime
upgrade must be performed and certified inside the Agent repository without changing GA semantics implicitly.

## Platform — old pnpm lock

`pnpm install --frozen-lockfile` passed. Six independent test databases were migrated on disposable MySQL 8.4. Hub tests used
disposable MongoDB 7 and MinIO.

| Command | Result |
|---|---|
| `pnpm test` | FAIL — root DDD gate: `kokoro-site/src/bootstrap` is an unapproved top-level entry; 4/5 root tests pass |
| `pnpm -r --filter '@kokoro/*' test` | PASS — 1,038 package unit tests |
| `pnpm typecheck` | PASS — root plus eight workspace packages |
| `pnpm lint` | FAIL — four `no-undef` findings in `scripts/integration-dev.mjs` (`process`/`console`) |
| `pnpm db:migrate` with six disposable databases | PASS — all current migrations applied |
| `pnpm test:integration` with MySQL/Mongo/MinIO | PASS — 569 tests across current integration scripts |

The first integration attempt intentionally remains part of the diagnostic record: Hub's 16 upload tests failed when MinIO endpoint
and credentials were omitted. Re-running the Hub gate with explicit test-only configuration passed 115/115, and the complete matrix
then passed 569/569. This proves the dependency is real and fail-loud rather than a product regression.

## Session — old `package-lock.json`

| Command | Result |
|---|---|
| `npm ci` | PASS, but npm audit summary reports 2 high-severity dependency vulnerabilities |
| `npm test` with disposable Redis/Mongo | PASS — 29 files passed, 1 skipped; 381 tests passed, 8 skipped |
| `npm run typecheck` | PASS |
| `npm run lint` | PASS |

## Web — old pnpm workspace lock

| Command | Result |
|---|---|
| `pnpm install --frozen-lockfile` | PASS |
| `pnpm test` | PASS — i18n 12, Admin 25, User 484 tests |
| `pnpm typecheck` | PASS — i18n, Admin, User |
| `pnpm lint` | FAIL — `@kokoro/i18n` cannot resolve its declared `eslint` executable under isolated linking |

## Accepted baseline reds and their owning task

| Baseline red | Root cause | Planned owner |
|---|---|---|
| Platform DDD layout | seed composition entry under broad top-level `bootstrap` | Platform repository: move Site seed to `interfaces/cli`; do not widen the DDD allowlist |
| Platform root lint | root integration script lacks an explicit Node lint environment | Platform repository lint gate |
| Web i18n lint | leaf executable declaration is missing under isolated linker | Web repository workspace gate |
| Agent ruff/pyright | three stale imports plus import ordering in tests | Agent repository compatibility gate; no GA runtime semantic source change |
| Session dependency audit | two high-severity findings in the old npm resolution | Session repository dependency/security gate |

No red result in this table may be described as a new Wave 0 regression. It must either be resolved by the named task or remain an
explicitly accepted, time-bounded exception in the final evidence.

---

# Final converged evidence (2026-07-27)

This section closes the baseline above. Every number below was observed in this run; nothing is copied forward as assumed.

## Promotion

Atomic pin promotion commit: `0f30276146fbde276da9569bab87205695690c94`
(`build(repository): promote verified wave 0 pins`), containing exactly five paths — the pin manifest and the
four gitlinks. No toolchain, contract or business change shares this commit.

| Repository | Promoted pin | Recoverable ref | Child remote CI |
|---|---|---|---|
| Agent | `e01b6eab3e4b8b9b1fc193c53590e3ca564c2b51` | `refs/tags/kokoro-wave0-foundation-2026-07-27-agent` | run `30203330241` success |
| Platform | `fe5b755f7b1a98247f33e3318f4ade9c4ae87f18` | `refs/tags/kokoro-wave0-foundation-2026-07-27-platform` | run `30203426690` success |
| Session | `c24080c117aeafa3ec02db1700549057218baefa` | `refs/tags/kokoro-wave0-foundation-2026-07-27-session` | run `30203819683` success |
| Web | `1934383ea4a72be9f2cc664af5de62b46c77c81c` | `refs/tags/kokoro-wave0-foundation-2026-07-27-web-2` | run `30204922834` success |

The superseded Web candidate tag `kokoro-wave0-foundation-2026-07-27-web` (`fdf73b5`) was left in place and not moved.

## Root Infra runtime compatibility gate

Run against the staged pin combination before the promotion commit existed, using the root Infra authority
(`scripts/infra/manager.mjs`, profile `full`, scope `ci-federated`, mode `ci`) — no ad-hoc containers, which is the
defect the baseline section above recorded.

```text
outcome: pass          reasonCode: ok         treeMode: index
combinationId:     wave1-federated-ci-2026-07-27
startedAt:         2026-07-27T14:34:00.306Z
completedAt:       2026-07-27T14:35:27.250Z   durationMs: 86944
combinationDigest: f5be9e5cf53b0cc3603cfa064d1bcdf40476f2287505da8e6ba6584cdf60b3e9
manifestDigest:    2482f7ff5f7f3f7b04c2a8a2528daa6f92cb44ddb73282d5957af9539535a919
matrixDigest:      4b9b8a397248f4bbf0a6c28030f03fc12fed28ddbc63c078e9ff02e3456b9c32
preflightPinVerification: pass    postflightPinVerification: pass
services healthy: mysql, redis, mongo, minio, litellm
```

| Scenario | Participants | Outcome | ms |
|---|---|---|---:|
| `web-session-http-sse` | session → web | pass | 9120 |
| `session-platform-internal-rpc` | platform → session | pass | 2938 |
| `session-agent-durable-localfake` | agent → session | pass | 2549 |
| `agent-model-gateway-localfake` | platform → agent | pass | 3781 |
| `platform-admin-auth-connect` | platform → web | pass | 5845 |

Infra was stopped in a trap, the five containers were removed, and `docker ps -a` reported zero containers
afterwards. No volume and no image was deleted.

## Clean recursive clone replay

Root was cloned over the `file://` transport with `--no-local`, so the clone has an independent object database
(`.git/objects/info/alternates` absent — verified). The four children were initialised from their own GitHub
remotes, not from local worktrees.

| Gate | Result |
|---|---|
| `verify-federated-repositories --tree head --remote` | PASS — 4 repositories |
| `contract/check.py` | PASS — 19 generated mirrors match |
| `pytest contract/tests -q` | PASS — 35 tests |
| `buf format --check`, `buf lint` | PASS |
| `check-generated-contracts.mjs` | PASS — generated RPC mirrors match |
| `node --test scripts/architecture/*.test.mjs` | PASS — 15 tests |
| `check-index-coverage.ts` | PASS — 57 roots |
| `check-dependencies.ts` | PASS — 57 roots, 13 internal package edges |
| `node --test scripts/repository/*.test.mjs scripts/compatibility/*.test.mjs scripts/foundation/check-evidence.test.mjs` | PASS — 72 tests |
| `pytest scripts/compatibility/test_*.py -q` | PASS — 6 tests |
| contract regenerated twice, then `git diff --exit-code` in root and all four children | PASS — deterministic, clean tree |

## Rollback rehearsal

Performed on a throwaway branch inside the disposable replay clone; never pushed, and `git reset` was never used
on a working repository.

- `git revert` of the promotion commit produced `f887f3b`, touching the same five paths.
- `git submodule update --init --recursive` restored the four previous pins
  (`c2a92c8` / `0463513` / `ffc9b39` / `da32035`).
- `verify-federated-repositories --tree head --remote` PASSED on the reverted tree.
- All four *previous* recoverable tags still resolve on their remotes, so the rollback target is anchored:
  `kokoro-wave1-federated-ci-2026-07-27-agent`, `kokoro-admin-auth-connect-2026-07-27-platform`,
  `kokoro-platform-admission-boundary-2026-07-27-session`, `kokoro-admin-auth-connect-2026-07-27-web`.

## Baseline reds — final disposition

| Baseline red | Disposition |
|---|---|
| Platform DDD layout (`kokoro-site/src/bootstrap`) | Resolved in Platform: seed moved to `interfaces/cli`; the DDD allowlist was not widened |
| Platform root lint (`scripts/integration-dev.mjs`) | Resolved in Platform lint gate; child CI green |
| Web i18n lint executable resolution | Resolved in Web: leaf declares its own ESLint under the isolated linker; i18n lint runs |
| Agent ruff/pyright stale imports | Resolved in Agent with no GA runtime semantic change; Ruff + Pyright green |
| Session dependency audit (2 high) | Resolved in Session: `npm audit` reports 0 vulnerabilities |

All five baseline reds are closed in their owning repository, each with its own green remote CI run recorded above.

## Toolchain actually used for this closure

| Tool | Observed version |
|---|---|
| Git | `2.39.5 (Apple Git-154)` |
| Node.js | `22.22.2` |
| pnpm | `11.2.2` |
| uv | `0.10.4` |
| Root Python | `3.13.5` |
| Docker Engine | `28.5.1` |

## Still open after this closure

These are recorded as open, not as passed:

1. Root feature branch remote CI on the exact promoted SHA. Root CI evidence is an external artifact and is not
   claimed by this document.
2. Root BOM tag creation and remote tag-object verification.
3. `kokoro-agent` has no `.python-version`; `requires-python = ">=3.11"` resolved to CPython `3.14.3` in the
   replay clone while child CI uses `3.11`. The same lock therefore runs under different interpreters depending
   on host. Determinism gap owned by the Agent repository.
4. Internal RPC coverage is 1 of 5 declared contracts. Only `platform-admin-auth v1` is protobuf/Connect; the
   remaining internal calls stay on JSON/Zod mirrors plus `callService`. See
   [architecture survey](../../2026-07-27-kokoro-architecture-survey.md) §3.
5. Session `legacy-admission-adapter.ts` unknown/not_found still lacks a real Admission RPC — Wave 3, not Wave 0.
