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
