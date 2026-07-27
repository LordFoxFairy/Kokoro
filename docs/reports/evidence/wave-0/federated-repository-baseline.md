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

---

# Round 2 — hardening promotion (2026-07-27)

Two children advanced past the first promotion; Session and Web are unchanged and keep their round-1 pins.

Promotion commit: `06997bd0e5a26c34ed25c3f185ce4dde7412060f` (`build(repository): promote wave 0 hardening pins`),
four paths: the manifest, the compatibility matrix `combinationId`, and the two moved gitlinks.

| Repository | Pin | Recoverable ref | Child CI |
|---|---|---|---|
| Agent | `9d3180e5b26b25d2ef8ce9c42636ef18a3305204` | `refs/tags/kokoro-wave0-hardening-2026-07-27-agent` | success |
| Platform | `f0fd2e4e1e1de1017e0ad5dfacf42e1135576487` | `refs/tags/kokoro-wave0-hardening-2026-07-27-platform` | success |

Both new tags are annotated and their peeled SHA was verified against the pin on the remote.

## What changed and why

**Agent** — added `.python-version` (3.11). The repository had no interpreter pin and its CI installs uv without a
`python-version` input, so `uv sync --locked` resolved whichever interpreter the runner offered; a clean clone here
picked CPython 3.14.3 against a lock whose recorded baseline was 3.11. Anchored to the four agreeing in-repo
declarations: `Dockerfile: FROM python:3.11-slim`, Pyright `pythonVersion`, Mypy `python_version`, and the
`requires-python` lower bound. `uv.lock` is byte-identical and no `src/` file changed, so GA semantics are untouched.
Verified: Ruff clean, Pyright `0 errors, 0 warnings, 0 informations`, pytest `609 passed, 1 skipped` — matching the
recorded baseline, with the single skip environmental (`parent-repo examples not present`) and announced.

**Platform** — `callService` now requires an explicit `caller`, and the unreachable shared-secret fallback module
`internal-secret-guard.ts` was deleted along with its public re-export. All six production call sites already passed a
caller and `route-access` answers 401 without the header, so the fallback had zero consumers. Unit tests move
`1,082 → 1,076`; the delta is exactly the six cases in the deleted module's own test file, with every other package
unchanged. Integration is `603 passed / 0 failed` across eight packages.

Two documentation defects found by the INDEX audit were fixed in the same commit: `platform-kit/INDEX.md` now
enumerates its six export subtrees instead of asserting only that `src/index.ts` is supported, and `src/rpc/INDEX.md`
now states that Connect covers `platform-admin-auth v1` alone. `callService` had appeared in none of the 58 INDEX
files, so the RPC component read as evidence that internal traffic had already migrated.

## A silent skip that had never run in CI

`kokoro-platform-admin/test/integration/admin-auth-prisma.test.ts` guarded itself with `describe.skipIf`, requiring a
database literally named `kokoro_admin_verify`. Platform CI provisions `kokoro_admin_test` under its `<service>_test`
convention, so **those five tests had never executed in CI while the workflow reported green**. Converting the guard to
fail-loud surfaced this immediately as a red run. The guard now accepts either admin-only throwaway database and still
refuses shared ones, because the suite truncates operator/auth tables. Verified both directions: with the CI name the
five tests execute (12 passed), and a shared database is refused rather than skipped.

## Round 2 runtime compatibility gate

```text
outcome: pass       treeMode: index      durationMs: 83292
combinationId:     wave0-hardening-2026-07-27
combinationDigest: e9f70fa06605aba4d53dfb4347f8671bc62e3d7a7cb9b035deec31612fcba73e
manifestDigest:    10d9c1bd341738b3320831f8ff2c310ec208e97577c69e2b5d7dec74acde374a
matrixDigest:      ff8457799946a62f2732400e34f6dfc80c6a85dc880a87515fea294d9e096fdd
preflightPinVerification: pass    postflightPinVerification: pass
```

| Scenario | Outcome | ms |
|---|---|---:|
| `web-session-http-sse` | pass | 7361 |
| `session-platform-internal-rpc` | pass | 2538 |
| `session-agent-durable-localfake` | pass | 2631 |
| `agent-model-gateway-localfake` | pass | 4776 |
| `platform-admin-auth-connect` | pass | 2830 |

## New root governance in this round

- `contract/registry/boundaries.yaml` records all five boundaries and their 77 operations against their real contract
  sources, gated by `scripts/contract/check-boundary-registry.mjs` and wired into root CI. It reports two facts the
  codebase could not previously measure: **46 operations derive `siteId` from a hop-level header and none carry it as a
  request field**, and `model-gateway` has no machine-readable contract source. Both appear in the success line as
  counted debt rather than being silently blessed. The gate was verified to reject source-missing, unstructured
  site-scope, operation-orphan and namespace-axis-pollution mutations.
- The INDEX coverage gate now requires a concrete backticked entrypoint in `Public boundary`, rejects empty sections,
  permits `N/A` only with a stated reason, and validates link anchors.

## Open after round 2

1. Root remote CI has never run: the repository has zero Actions secrets, so `contract.yml` fails on its own
   `KOKORO_SUBMODULE_TOKEN` guard. Owner action; no root BOM tag until a green run exists.
2. Both `uv.lock` files pin every artifact URL to an Aliyun mirror (agent 1821 / root 29, zero canonical PyPI), which
   is what timed out the first agent CI run. A plain re-resolve fixes the URLs but mass-upgrades roughly sixty
   packages including `langgraph`, `langchain-core`, `deepagents`, `protobuf` 6→7 and `wrapt` 1→2, plus a `websockets`
   downgrade — an unapproved GA dependency change. Requires a constraints-pinned re-lock proving zero version drift.
3. Subrepo INDEX findings from the audit (5 Critical / 9 Important / 10 Minor) are partly addressed; the remainder
   needs its own promotion round.

---

# Round 3 — index truth and canonical locks (2026-07-27)

Promotion commit: `5e4747c08814cbb30f3e806f738228f14ec5666a`. All four children moved; each child CI was green on the
exact promoted SHA before its tag was cut, and every tag's peeled SHA was verified against the pin on the remote.

| Repository | Pin | Recoverable ref |
|---|---|---|
| Agent | `5c118e59f3a8bf6adcbe2a8f984021029b6ae9ca` | `refs/tags/kokoro-wave0-index-truth-2026-07-27-agent` |
| Platform | `92a293d68ce41a0e10497b217c52e04f787c7cd3` | `refs/tags/kokoro-wave0-index-truth-2026-07-27-platform` |
| Session | `be2174d1c01b4d9016d84ace7c6394e13a637c76` | `refs/tags/kokoro-wave0-index-truth-2026-07-27-session` |
| Web | `b65e86d39767636362ae253147b5d7925616ea03` | `refs/tags/kokoro-wave0-index-truth-2026-07-27-web` |

## Canonical dependency sources

Both `uv.lock` files resolved every artifact URL through a local mirror, which is what timed out an earlier Agent CI
run. Re-resolved under constraints derived from the existing locks, so only the source host changed:

| Lock | Mirror URLs | Canonical URLs | Version drift |
|---|---:|---:|---|
| root | 29 → 0 | 0 → 22 | none |
| agent | 1821 → 0 | 0 → 1686 | none |

Deleting a lock to force re-resolution discards uv's version preferences and would have upgraded roughly sixty
packages including `langgraph`, `langchain-core`, `deepagents`, `protobuf` 6→7 and `wrapt` 1→2, with a `websockets`
downgrade. The constraints reproduce the recorded resolution exactly. Because the Agent lock is universal, `numpy`
legitimately resolves to both `2.4.6` and `2.5.0` under different markers, so multi-version packages are capped
rather than pinned — pinning both is unsatisfiable.

Two limits are recorded rather than papered over. An in-repo `[[tool.uv.index]]` does **not** override a user-level
default index on uv 0.10.4, so locking on a mirror-configured machine still requires `UV_NO_CONFIG=1`. And any `uv`
command run without `--locked` silently re-resolves and rewrites the lock, which is how an earlier attempt committed
mirror URLs while claiming to have removed them; the committed bytes must be checked with `git show <sha>:uv.lock`.

## INDEX accuracy

A full audit of all 58 INDEX files produced 5 Critical, 9 Important and 10 Minor findings. Each repository was fixed
by one agent and then checked by an independent reader that re-derived the public surface from the real
`index.ts` / `__all__` rather than trusting the report. Three claims were rejected on that pass and corrected: an
assertion that every non-Connect call goes through `callService` (the Admin gateway issues raw `fetch` at four
sites), a leftover "was removed once it had zero consumers" narrative, and two modules naming an unimplemented
Platform Admission as a current caller.

Substantive mismatches the review found in the code itself: `kokoro-site/src/index.ts` does not re-export
`createSiteServer` although the other four modules export their `create*Server`, and `kokoro-user/src/index.ts`
omits `RefreshService` entirely. `skills/__init__.py` does not export `PackageStore`, `make_package_store` or
`ExecCapableBackend`, yet `worker/main.py`, `agents/deps.py` and `tools/deliver.py` deep-import them; that INDEX now
records the open boundary gap instead of describing it as a supported surface.

The coverage gate then rejected the four newly added Web UI maps as unregistered roots, which is the gate behaving
correctly. Registering them takes the architecture manifest from 58 to **62 roots**.

## Round 3 runtime compatibility gate

```text
outcome: pass       treeMode: index      durationMs: 86628
combinationId:     wave0-index-truth-2026-07-27
combinationDigest: e3009fbd2765343d23858169109a8f599caa4a92b459ebe8bec486e6f76d03c0
manifestDigest:    526fed2fe357b6534cebc47759860f9caf3ffa3ba35ba2271408d06e44714962
matrixDigest:      393e5d8974fb5d50f4959e65d2fb314b675e58556b1079d9f7a6c5cc179b0866
preflightPinVerification: pass    postflightPinVerification: pass
```

| Scenario | Outcome | ms |
|---|---|---:|
| `web-session-http-sse` | pass | 7536 |
| `session-platform-internal-rpc` | pass | 2610 |
| `session-agent-durable-localfake` | pass | 6804 |
| `agent-model-gateway-localfake` | pass | 3838 |
| `platform-admin-auth-connect` | pass | 2902 |

Infra ran under the root authority and was stopped in a trap; zero containers remained and no volume or image was
removed.

## Still open

1. Root remote CI has never run — the repository has no Actions secrets, so `contract.yml` stops at its own
   `KOKORO_SUBMODULE_TOKEN` guard. Owner action. No root BOM tag until a green run exists.
2. Wave T2 (Public Admin API over OpenAPI 3.1) has not started.
3. Removing `default = true` from the user-level uv configuration would make canonical locking the default instead
   of something each locking session has to remember.
