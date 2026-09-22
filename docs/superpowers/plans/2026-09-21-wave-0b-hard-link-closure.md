# Wave 0B Hard-Link Closure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the current BFF→Capability and BFF↔Scheduler hard links, delete BFF's dead Storage HTTP call, and leave every identity-dependent Storage consumer explicitly gated for Wave 2 after Wave 1 IAM admission.

**Architecture:** Capability and Scheduler remain contract owners. BFF vendors immutable owner blobs, generates consumer boundaries, and deletes stale routes in the same consumer slice. Root activates an edge only after pushed gitlinks, exact consumer/producer versions, full fan-out digests, generated drift checks, and isolated real-process smoke pass. W0B does not activate Storage: authorization depends on Wave 1 and the complete Proto v2 cutover belongs to Wave 2.

**Pinned toolchain:** BFF Node `22.22.2`, Capability Node `24.20.0`, pnpm `11.25.0`, TypeScript `5.9.3`, `@hey-api/openapi-ts` `0.99.0`, Zod `4.5.4`, Prettier `3.9.6`, Scheduler Go `1.26.8`, Root Python 3 + pytest + Ruff `0.15.2`.

## 1. Global constraints

1. Root begins at `bfa054f3cafe0e340a8e04d567bf923dbe03ee4e`. Every task records its actual start SHA, `main`, clean status, files, executor, reviewer, delivery SHA and remote SHA.
2. One repository has one writer. Owner → consumer → Root slices are serial. Reviewers are read-only. Root task/progress/index and Git index remain Root-owned.
3. Child commits must be reviewed, fully verified and pushed to `origin/main` before Root lifts a gitlink. Root executes `test "$(git -C REPO rev-parse HEAD)" = "$(git -C REPO ls-remote origin refs/heads/main | cut -f1)"`.
4. A Root gitlink lift refreshes every inventory owner/evidence/version reference to that child from exact commit blobs, including unrelated broken edges. Non-target edge state cannot change.
5. One operation has one transport. No alias, fallback, dual path, copied editable owner contract, stale generated output or sibling source import survives a release commit.
6. Capability W0B transport is read-only HTTP `/v1/*`. Wave 3 atomically replaces it with `kokoro.platform.v1` ConnectRPC. BFF never uses the old Capability execution RPC.
7. Capability public query decision is frozen now: BFF exposes and forwards only canonical `query`; public `q` is rejected with `400 invalid_query_parameter`. There is no `q` alias.
8. Scheduler owns control and event contracts. W0B activates BFF control and the BFF receiver only. `EDGE-SCHEDULER-AGENT` stays broken until trusted Agent callback identity is approved.
9. Inventory `code_generator_version` and `runtime_package_version` describe the contract consumer. For Scheduler→BFF the consumer is the BFF webhook receiver. Producer-owned event edges additionally require `producer_runtime_assertions`; Scheduler Go evidence never replaces BFF receiver generator/Node evidence.
10. Storage edges stay broken. W0B deletes `/internal/bff/library`; W1 owns trusted IAM admission; W2 owns list RPCs, default-deny caller×operation×scope policy and all three Proto v2 consumers.
11. PostgreSQL/Redis/process setup failure leaves the task at `待集成验证` and its edge `broken`. Mock-only tests are not integration evidence. A runner may delete only databases, Redis keys and process groups created under its random run ID.
12. W0B changes no canonical database schema and no data owner. Any discovered schema requirement stops the task and returns to design review.
13. Scratch files under `.superpowers/` are non-authoritative. Binding decisions live in this versioned plan, `docs/task.md` and `docs/progress.md`.

## 2. Exact toolchain commands

Run from the indicated repository; any mismatch blocks the task.

```bash
# BFF
BFF_NODE_BIN="$HOME/.nvm/versions/node/v22.22.2/bin"
env PATH="$BFF_NODE_BIN:$PATH" node --version              # v22.22.2
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm --version     # 11.25.0
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm exec tsc --version  # Version 5.9.3

# Capability
CAP_NODE_BIN="$HOME/.nvm/versions/node/v24.20.0/bin"
env PATH="$CAP_NODE_BIN:$PATH" node --version              # v24.20.0
env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm --version     # 11.25.0
env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm exec tsc --version  # Version 5.9.3

# Scheduler
go env GOVERSION GOTOOLCHAIN                                # go1.26.8 / auto
```

`corepack pnpm` is used in every Node command below. A failed Corepack fetch or Go toolchain acquisition is a blocker, not a reason to use another version.

BFF full gate after Task 4 adds `format:check`:

```bash
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm format:check
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm lint
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm typecheck
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm contract:check
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm test
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm test:integration
env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm build
```

Root full gate:

```bash
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-w0b-ten-repo.json  # expected exit 1; record 110/current count honestly
python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/CHECKPOINT.json
git diff --check
```

The ten-repository audit remains an honest debt gate. Task-specific Ruff commands target only files created or modified by that task, so unrelated pre-existing formatting debt cannot be hidden or swept into the slice. `verify-contract-checkpoint.py` is the executable compatibility oracle: it requires the exact active/broken/illegal IDs below and rejects any schema/gitlink/digest/evidence/version drift.

## 3. Compatibility checkpoints

| Checkpoint | Active IDs | Broken IDs | Illegal IDs |
| --- | --- | --- | --- |
| `w0b-start` | `EDGE-BROWSER-WEB` | `EDGE-WEB-BFF`, `EDGE-BFF-IAM`, `EDGE-BFF-SYSTEM`, `EDGE-BFF-CAPABILITY`, `EDGE-BFF-STORAGE`, `EDGE-BFF-AGENT`, `EDGE-BFF-SCHEDULER`, `EDGE-BFF-BILLING`, `EDGE-AGENT-SYSTEM`, `EDGE-AGENT-CAPABILITY`, `EDGE-AGENT-STORAGE`, `EDGE-CAPABILITY-STORAGE`, `EDGE-CAPABILITY-IAM`, `EDGE-SCHEDULER-BFF`, `EDGE-SCHEDULER-AGENT` | `EDGE-WEB-IAM-DIRECT` |
| `w0b-capability` | `EDGE-BROWSER-WEB`, `EDGE-BFF-CAPABILITY` | `EDGE-WEB-BFF`, `EDGE-BFF-IAM`, `EDGE-BFF-SYSTEM`, `EDGE-BFF-STORAGE`, `EDGE-BFF-AGENT`, `EDGE-BFF-SCHEDULER`, `EDGE-BFF-BILLING`, `EDGE-AGENT-SYSTEM`, `EDGE-AGENT-CAPABILITY`, `EDGE-AGENT-STORAGE`, `EDGE-CAPABILITY-STORAGE`, `EDGE-CAPABILITY-IAM`, `EDGE-SCHEDULER-BFF`, `EDGE-SCHEDULER-AGENT` | `EDGE-WEB-IAM-DIRECT` |
| `w0b-exit` | `EDGE-BROWSER-WEB`, `EDGE-BFF-CAPABILITY`, `EDGE-BFF-SCHEDULER`, `EDGE-SCHEDULER-BFF` | `EDGE-WEB-BFF`, `EDGE-BFF-IAM`, `EDGE-BFF-SYSTEM`, `EDGE-BFF-STORAGE`, `EDGE-BFF-AGENT`, `EDGE-BFF-BILLING`, `EDGE-AGENT-SYSTEM`, `EDGE-AGENT-CAPABILITY`, `EDGE-AGENT-STORAGE`, `EDGE-CAPABILITY-STORAGE`, `EDGE-CAPABILITY-IAM`, `EDGE-SCHEDULER-AGENT` | `EDGE-WEB-IAM-DIRECT` |

Expected raw compatibility counts are respectively `1/15/1`, `2/14/1`, and `4/12/1`; counts alone never pass the gate.

## 4. Vendor and generation contract

Each BFF dependency manifest has this exact top-level schema:

```json
{
  "schema_version": 1,
  "status": "design-frozen-or-generated",
  "owner": {
    "repository_path": "apps/OWNER",
    "repository_commit": "40_HEX",
    "contract_version": "VERSION",
    "contract_path": "PATH",
    "contract_sha256": "64_HEX"
  },
  "generator": {
    "package": "@hey-api/openapi-ts",
    "version": "0.99.0",
    "config_path": "CONFIG_PATH",
    "config_sha256": "64_HEX"
  },
  "runtime": { "node": "22.22.2", "pnpm": "11.25.0", "zod": "4.5.4" },
  "lockfile_sha256": "64_HEX",
  "generated": [{ "path": "EXACT_PATH", "sha256": "64_HEX" }]
}
```

`design-frozen` may have an empty `generated` array; the implementation commit must change it to `generated` and list every output. Owner bytes are copied only from a commit blob:

```bash
git --no-replace-objects -C ../OWNER show --end-of-options "$OWNER_SHA:$OWNER_PATH" > "$VENDOR_PATH"
printf '%s  %s\n' "$OWNER_SHA256" "$VENDOR_PATH" | shasum -a 256 -c -
```

Both generator configs use the exact IAM-proven pattern: TypeScript + Zod 4 + bundled fetch client + flat SDK, clean output, `.js` module extensions, no production generation and no extra `@hey-api/client-fetch` package. Each `contract:check:*` regenerates into a temporary directory, asserts the following exact allow-list, byte-compares it and rejects extra/missing/manual files:

```text
client.gen.ts
client/client.gen.ts
client/index.ts
client/types.gen.ts
client/utils.gen.ts
core/auth.gen.ts
core/bodySerializer.gen.ts
core/params.gen.ts
core/pathSerializer.gen.ts
core/queryKeySerializer.gen.ts
core/serverSentEvents.gen.ts
core/types.gen.ts
core/utils.gen.ts
sdk.gen.ts
types.gen.ts
zod.gen.ts
```

An active request edge pins: dependency manifest, vendor artifact, generator config/script, all generated allow-list files, facade, behavior test, `package.json`, `pnpm-lock.yaml`, `.node-version`. Scheduler→BFF additionally pins the receiver validator/route/test and Scheduler `go.mod` as producer runtime evidence.

---

## Chunk 1 — Freeze plan and evidence machinery

### Task 0: Freeze the W0B control plane

**Repository/writer:** Root / Root controller. **Reviewer:** architecture reviewer + execution reviewer. **Start:** `bfa054f3...`.

**Exact files:** create `docs/superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md`; modify `docs/task.md`, `docs/progress.md`, `docs/INDEX.md`. No child file or gitlink.

1. Obtain clean `SPEC ✅` and `EXECUTION ✅`, each `Blocking/Important/Minor = 0/0/0`.
2. Point `docs/task.md` and `docs/INDEX.md` to this plan. Split W0B into the exact task cards below; only Task 0 becomes `已验收`.
3. Append audit/review facts and frozen Root SHA to `docs/progress.md`.
4. Run `python3 scripts/verify-repository-topology.py`, `python3 -m pytest scripts/tests -q`, and `git diff --check`; all exit `0`.
5. Commit exactly `docs(governance): freeze wave 0b execution plan`, push, and require clean `main == origin/main`.

### Task 1: Add consumer/producer version parsing and executable checkpoints

**Repository/writer:** Root / one Root governance subagent. **Reviewer:** fresh Root verifier reviewer.

**Exact files:**
- modify `scripts/governance/contract_inventory.py`
- create `scripts/governance/contract_checkpoint.py`
- create `scripts/verify-contract-checkpoint.py`
- modify `scripts/tests/test_contract_compatibility.py`
- create `scripts/tests/test_contract_checkpoint.py`
- create `verification/contracts/checkpoints/w0b-start.json`
- create `verification/contracts/checkpoints/w0b-capability.json`
- create `verification/contracts/checkpoints/w0b-exit.json`
- modify `verification/contracts/README.md`
- modify `scripts/INDEX.md`
- exclude inventory data, gitlinks, child repos and control docs

1. RED: add tests for exact `.node-version` (`plain-version-file`), canonical `go.mod` (`go-mod`), missing/wrong producer assertion, wrong producer owner, invalid UTF-8, range values, dirty tree, replace refs, mismatched gitlink, count-preserving ID swaps and unexpected verifier drift.
2. Run `python3 -m pytest scripts/tests/test_contract_compatibility.py scripts/tests/test_contract_checkpoint.py -q`; capture non-zero RED.
3. Implement stdlib-only parsers. Every active edge requires exactly one consumer-runtime assertion. When generation applies it also requires exactly one managed consumer-generator assertion; preserve only the existing `not-applicable:same-origin-route` exemption for `EDGE-BROWSER-WEB`. Active `http-event` edges never receive that exemption and additionally require exactly one `producer_runtime_assertion` bound to the contract producer repository. Never parse composite `A+B` values.
4. Implement checkpoint CLI to compare exact ID/state sets, invoke the compatibility verifier, accept only declared broken/illegal outcomes, and reject every other error.
5. GREEN:
   ```bash
   python3 -m pytest scripts/tests/test_contract_compatibility.py scripts/tests/test_contract_checkpoint.py -q
   python3 -m pytest scripts/tests -q
   python3 -m ruff format --check scripts/governance/contract_inventory.py scripts/governance/contract_checkpoint.py scripts/verify-contract-checkpoint.py scripts/tests/test_contract_compatibility.py scripts/tests/test_contract_checkpoint.py
   python3 -m ruff check scripts/governance/contract_inventory.py scripts/governance/contract_checkpoint.py scripts/verify-contract-checkpoint.py scripts/tests/test_contract_compatibility.py scripts/tests/test_contract_checkpoint.py
   python3 -m py_compile scripts/governance/contract_inventory.py scripts/governance/contract_checkpoint.py scripts/verify-contract-checkpoint.py
   python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-start.json
   git diff --check
   ```
6. SPEC/QUALITY review; commit `test(contracts): verify consumer and producer runtimes`; push and record SHA.

---

## Chunk 2 — Capability current-state closure

### Task 2: Verify the Capability owner release

**Repository:** `apps/kokoro-capability`. **Writer:** none unless drift is found. **Reviewer:** Capability owner reviewer.

**Accepted owner:** the initial frozen release `e576d38dd103c2fda4d6389385b3f04f82ddfc20` failed runtime/contract/docs parity and opened the separate W0B-2A owner repair. The accepted release is commit `7f89a267d745cbb9870f52d6edb23dec1a3c469b`; `contract/openapi/capability-http.openapi.json`; version `2.0.0`; direct SHA-256 `e0b7c4b57ac030efb73878b51da2a3595ec0172bce0608a88ea925b57a69761a`; combined provenance `536dca2989a5a9b7e06f1bcd15ef8eb25876ef4184345b077407555457e45c4b`.

1. Run the exact Capability toolchain preflight and verify clean `main`, Root gitlink, HEAD and `origin/main` all equal the frozen commit.
2. Read absolute `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, contract and canonical Prisma schema. Report no blocking contradiction and “no schema change”.
3. Run:
   ```bash
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm format:check
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm lint
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm typecheck
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm contract:check
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm exec vitest run test/contract/bff-projection.test.ts test/unit/bff-projection.test.ts test/integration/bff-projection.test.ts --no-file-parallelism
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm test
   env PATH="$CAP_NODE_BIN:$PATH" corepack pnpm build
   ```
4. Confirm only the four GETs `/v1/skills`, `/v1/skills/pool`, `/v1/skills/catalog`, `/v1/mcp/servers`; no `/bff/*`; query/header fields match the artifact.
5. Produce a read-only handoff with SHA, remote SHA, digest, versions, exact results and clean state. Drift creates a separate owner task; this card does not expand.

### Task 3: Freeze BFF Capability design and owner artifact

**Repository/writer:** `apps/kokoro-bff` / BFF Capability subagent. **Reviewer:** BFF design reviewer.

**Exact files:**
- create `contract/vendor/kokoro-capability/7f89a267d745cbb9870f52d6edb23dec1a3c469b/capability-http.openapi.json`
- create `contract/dependencies/capability-http.json` with `status=design-frozen`
- create `openapi-ts.capability.config.ts`
- modify `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/CURRENT.md`
- modify `test/contract-governance.test.mjs`, `test/architecture.test.ts`
- exclude runtime source, package/lock, public OpenAPI and database schema

1. RED tests require exact owner tuple/digest, read-only provenance, HTTP-only boundary, canonical public `query`, rejection of `q`, Wave 3 deletion owner and no data-owner/schema change.
2. Copy the artifact using the commit-blob command in §4 and verify its frozen digest.
3. Update the three-document gate before runtime code; unresolved owner/query/data decisions block Task 4.
4. Run:
   ```bash
   env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm build
   env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm exec node --test test/contract-governance.test.mjs test/architecture.test.ts
   env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm contract:check
   git diff --check
   ```
5. Review; commit `docs(bff): freeze Capability projection consumer design`; push.

### Task 4: Implement the generated BFF Capability consumer

**Repository/writer:** BFF / same Capability subagent. **Reviewer:** fresh implementation reviewer. **Start:** Task 3 remote SHA.

**Exact files:**
- modify `.node-version`, `package.json`, `pnpm-lock.yaml`
- modify `openapi-ts.capability.config.ts`; create `scripts/generate-capability-http-client.mjs`
- create only the §4 allow-list under `src/generated/capability-http/`
- create `src/infrastructure/clients/capability/client.ts`, `src/infrastructure/clients/capability/errors.ts`, `src/infrastructure/clients/capability/types.ts`
- modify `src/http/routes/owner.ts`, `src/application/projections.ts`
- modify `contract/dependencies/capability-http.json` to `status=generated`
- modify `contract/openapi/v1/openapi.yaml`, `contract/tests/v1-operations.json`
- create `test/capability-client.test.ts`
- modify `test/bff.test.ts`, `test/contract-governance.test.mjs`, `test/architecture.test.ts`
- modify `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/CURRENT.md` to replace the design-frozen/future-tense state with the implemented current state
- no config, composition, database or unrelated docs file

1. Pin exact dev dependencies `@hey-api/openapi-ts@0.99.0`, `prettier@3.9.6`, `typescript@5.9.3`; exact runtime `zod@4.5.4`; add `format:check`, `contract:generate:capability`, `contract:check:capability`, and include drift check in `contract:check`.
2. RED: assert the four `/v1/*` paths, canonical `query`, `q` rejection, query allow-lists, trusted `web-bff` headers, 400/401/503 mapping, cursor-scope failure, 5s timeout, 1 MiB cap, drift rejection and absence of `/bff/*`.
3. Run focused RED: `env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm build && env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm exec node --test test/capability-client.test.ts test/bff.test.ts test/contract-governance.test.mjs test/architecture.test.ts`; capture non-zero.
4. Generate from the vendored blob; facade contains all wire mapping and generated types do not escape the adapter. Update the manifest with exact output/config/lock digests.
5. Run the BFF full gate from §2 and:
   ```bash
   ! rg -n '/bff/(skills|mcp)' src test contract docs
   ! rg -n '(^|[?&])q=' src test contract docs
   git diff --check
   ```
6. Review; commit `fix(bff): align Capability projection client with owner v1 routes`; push; prove remote equality.

### Task 5: Implement the isolated Capability↔BFF smoke runner

**Repository/writer:** Root / Root smoke subagent. **Reviewer:** fresh reliability reviewer.

**Exact files:** create `scripts/e2e/run_capability_bff_smoke.py`, `scripts/tests/test_capability_bff_smoke.py`; modify `scripts/INDEX.md`. No gitlink, inventory or control docs.

1. Runner CLI is exactly:
   ```bash
   python3 scripts/e2e/run_capability_bff_smoke.py \
     --postgres-admin-url "$KOKORO_SMOKE_POSTGRES_URL" \
     --redis-url "$KOKORO_SMOKE_REDIS_URL" \
     --bff-node-bin "$HOME/.nvm/versions/node/v22.22.2/bin" \
     --capability-node-bin "$HOME/.nvm/versions/node/v24.20.0/bin"
   ```
2. RED tests cover missing flags, invalid URL schemes, command timeout, readiness timeout, child early exit, database/Redis ownership, signal escalation, log sanitization and cleanup-after-failure. Run `python3 -m pytest scripts/tests/test_capability_bff_smoke.py -q`; capture non-zero.
3. Implement a 24-hex run ID; create only `w0b_cap_<run>_{capability,bff}` databases; use Redis prefix `kokoro:w0b:capability:<run>:`; choose loopback ports; apply each owner schema; start built `dist/main.js` with exact Node binaries in new process groups; wait `/readyz` for at most 30 seconds; always drain/TERM/KILL owned groups and drop only owned resources.
4. Exactly eight cases through the real BFF process: `/v1/skills?query=` with a non-empty value returns 200 (also proves canonical forwarding), pool 200, catalog 200, MCP servers 200, `q` 400, missing BFF service auth returns the canonical `403 service_auth_failed`, bad owner service token maps to the documented upstream error, and invalid cursor returns 400. Empty owner data is valid; no fixture may bypass HTTP. The 403 expectation follows the live-only runtime, which requires `KOKORO_BFF_SHARED_SECRET`; 401 is not a reachable configured live state.
5. GREEN:
   ```bash
   python3 -m pytest scripts/tests/test_capability_bff_smoke.py -q
   python3 -m ruff format --check scripts/e2e/run_capability_bff_smoke.py scripts/tests/test_capability_bff_smoke.py
   python3 -m ruff check scripts/e2e/run_capability_bff_smoke.py scripts/tests/test_capability_bff_smoke.py
   python3 -m py_compile scripts/e2e/run_capability_bff_smoke.py
   # then the exact real CLI above; expected exit 0 and JSON {"status":"PASS","cases":8,...}
   ```
6. Review; commit `test(e2e): add isolated Capability BFF smoke`; push.

### Task 6: Integrate and activate `EDGE-BFF-CAPABILITY`

**Repository/writer:** Root / Root integration subagent. **Reviewer:** cross-repository reviewer.

**Exact files:** modify gitlink `apps/kokoro-bff`; modify `verification/contracts/consumer-inventory.json`, `docs/task.md`, `docs/progress.md`. Capability gitlink is unchanged unless Task 2 created a separately reviewed/pushed owner commit.

1. Lift only pushed child SHA and refresh every BFF fan-out reference/digest.
2. Pin all request-edge evidence listed in §4; set only `EDGE-BFF-CAPABILITY` active with npm generator assertion and BFF `.node-version` runtime assertion.
3. Re-run Task 5 real CLI, Root topology/tests/ten-repository audit, then `python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-capability.json`; all non-debt gates exit `0`.
4. Review; commit `fix(integration): activate BFF Capability projection edge`; push; require clean Root.

---

## Chunk 3 — Scheduler control and BFF receiver closure

### Task 7: Verify the Scheduler owner release

**Repository:** `apps/kokoro-scheduler`. **Writer:** none unless drift is found. **Reviewer:** Scheduler owner reviewer.

**Frozen owner:** commit `92bf9e7e6724c591bab4b7fa27f08d694b59a67e`; `contract/openapi/v1/openapi.yaml`; version `1.0.0`; SHA-256 `6ec2f6d5d71efa60b92bba1eb2dd0c81b7439734e2bc4450caa221e952e24183`.

W0B-7R owner repair 已完成：修复精确限于 `contract/README.md`、`contract/manifest.json`、`contract/openapi/v1/breaking-policy.json`、`contract/openapi/v1/openapi.yaml`、`internal/adapters/httpclient/client_test.go`、`internal/application/commands.go`、`internal/transport/http/handler.go`、`internal/transport/http/handler_test.go`、`test/contract/openapi_test.go` 与 `test/integration/postgres_test.go` 这 10 个文件。它只把现有 `schedule_not_found` / `schedule_already_exists` 机器码与 opaque idempotency key 逐字语义变成可执行契约，并增加 RFC3339Nano 边界证据；没有新 API shape、Schema、路径或 header。独立 SPEC/QUALITY 最终为 `0/0/0`；Root 在冻结 diff 和推送 commit 后各执行独占 PostgreSQL + Redis DB 7 的全量 race，均为 `135 pass / 0 fail / 0 skip`，提交后 contract-check、vet 和 build 也均通过。

W0B-7I Root 集成精确限于 Scheduler gitlink、`verification/contracts/consumer-inventory.json`、`scripts/tests/test_contract_compatibility.py`、`docs/CURRENT.md`、本计划、`docs/task.md` 与 `docs/progress.md` 七个 Root 文件。它前移全部 8 个 Scheduler owner/evidence tuple 及 commit-blob digest，不激活新 edge；聚焦 pin 测试按 inventory-only RED 再 test-pin GREEN 执行，最终 checkpoint/topology/Root tests 由 Root 主控在真实暂存 gitlink 后复验。

1. Run exact Go preflight; verify clean `main`, Root gitlink and remote equality.
2. Read absolute technical/API/data documents, contract and canonical schema. Confirm `/schedules/{name}`, `X-Kokoro-Tenant-Id`, `X-Kokoro-Scheduler-Schedule`, RFC3339/RFC3339Nano occurrence, opaque idempotency key, `schedule_not_found`, `schedule_already_exists`, and retry statuses `408/425/429/5xx`.
3. Run:
   ```bash
   ./scripts/contract-check
   test -z "$(gofmt -l .)"
   go vet ./...
   go test ./...
   go test -race ./...
   go build ./...
   ```
4. Produce the read-only structured handoff. Any drift becomes a new owner task.

### Task 7R2: Preserve durable duplicate-create outcomes in PostgreSQL

**Owner/writer:** Scheduler / `w0b7r2_scheduler_conflict_writer` (gpt-5.6-sol/high); independent reviewer; Root owns Git and release acceptance. **Baseline:** `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-scheduler`, main `92bf9e7e6724c591bab4b7fa27f08d694b59a67e`, clean. Root control baseline `33ab25b44778a750b33a1c2bdcf154dac1dac1fc`; Task10 four-file draft is frozen and excluded from this slice.

**Placement/document gate:** this is an existing PostgreSQL command adapter bug, not a new responsibility. `docs/TECHNICAL_DESIGN.md` §3 already requires durable already-exists outcomes, `docs/API_CONTRACT.md` §3/6 and `contract/openapi/v1/openapi.yaml` require replayable 409, and `docs/DATA_MODEL.md` §1/3/5 plus `database/schema.sql` name `uq_scheduler_schedule_tenant_name`. The three documents are consistent; their runtime implementation failed Root's real HTTP probe (200 then 500). No new schema, API, module or dependency is needed.

**Exact files:** `internal/adapters/postgres/commands.go` and `test/integration/postgres_test.go` only. Record a real PostgreSQL RED for same tenant/name with a different key; fix the INSERT with targeted `ON CONFLICT ON CONSTRAINT uq_scheduler_schedule_tenant_name DO NOTHING RETURNING`, mapping `pgx.ErrNoRows` to the existing domain already-exists result. Delete the obsolete exclusive 23505 helper/import. Do not pre-SELECT, catch arbitrary errors or suppress unrelated constraints. Verify one Schedule, two durable receipts, service reconstruction and exact original result/request ID replay; add bounded concurrent new-key coverage in the same test file.

**Resources/verification:** Root allocates an exclusive `kokoro_scheduler_test_w0b7r2_*` database with explicit public search_path; reuse Redis DB7, no shared resets. Run focused RED/GREEN, contract-check, gofmt check, vet, full test and race with zero skips, build and fresh schema/nonempty rejection. Root independently reviews and reruns on a separate fixture, then commits/pushes the two paths. Frozen OpenAPI/manifest/schema bytes must remain unchanged.

**Dependencies:** Task10 writer has stopped and cleaned its resources. After this release is accepted, resume that same writer with the new runtime SHA, remove the diagnostic private 409 receipt injection, and prove natural duplicate-create 409 through BFF outbox. Task11 lifts Scheduler as well as BFF gitlinks and all runtime/evidence tuples, including the Scheduler pin regression. BFF's immutable owner artifact remains the original published release only if its bytes/version/digest still match; runtime release and artifact provenance are recorded separately, never rewritten as if generated from another commit.

**Accepted release (2026-09-22):** `975dee59616a1e0eda609aa69283401344900d83`; independent SPEC/QUALITY 0/0/0; Root full/race 139/0/0, real HTTP 200/409/restart409, exact receipt replay, cleanup verified. Artifact/schema/dependency bytes unchanged.

### Task 8: Freeze BFF Scheduler design and owner artifact

**Repository/writer:** BFF / `w0b8_bff_scheduler_designer` (`gpt-6-astra`, high). **Reviewer:** independent BFF design reviewer; Root integrates. **Start:** main `2ed792586e89c035155938078d9b07f33af95abd`, clean/live-remote aligned; Scheduler prerequisite accepted in Root `7c9e7abfbf8a4af36d7f039ec93f863dfc66b63f`. Root owns index/commit/push and control documents. No shared fixture access is required in this design-only slice.

Reuse the existing BFF vendor/dependency/config locations rather than a Root contract center or an editable duplicate in BFF public OpenAPI. The immutable owner blob and BFF consumer mapping have different owners; no Schema change is allowed. Before declaring the three-document gate passed, inspect the existing receipt pending-reclaim behavior: if preserving same-key/different-digest rejection requires extending Task 9's runtime file list, report the smallest required change to Root first. Design acceptance must not silently assume absent fencing or cross-service atomicity.

**Exact files:**
- create `contract/vendor/kokoro-scheduler/92bf9e7e6724c591bab4b7fa27f08d694b59a67e/openapi.yaml`
- create `contract/dependencies/scheduler.json` with `status=design-frozen`
- create `openapi-ts.scheduler.config.ts`
- modify `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/CURRENT.md`
- modify `test/contract-governance.test.mjs`, `test/architecture.test.ts`
- exclude runtime source, package/lock, public OpenAPI and schema

1. RED governance tests require immutable owner provenance and producer-owned event protocol.
2. Copy/verify the commit blob using §4. Document control client and BFF receiver separately.
3. Freeze semantics: trusted tenant is always `X-Kokoro-Tenant-Id`; BFF-specific payload `tenant_id` remains an integrity field, must equal that trusted header, and a mismatch returns `400 invalid_scheduler_dispatch`; the body field is never used to establish identity. The opaque Scheduler key is stored unchanged; semantic digest is SHA-256 over trusted tenant + schedule + canonical RFC3339Nano occurrence + canonical JSON body; same key/different digest is 409; occurrence→Run ID is deterministic; response-unknown/restart cannot create a second Run.
4. Run BFF build, `node --test test/contract-governance.test.mjs test/architecture.test.ts`, `pnpm contract:check`, `git diff --check` with the exact BFF PATH form from Task 3.
5. Review; commit `docs(bff): freeze Scheduler owner contracts`; push.

### Task 9: Implement generated Scheduler control and receiver boundaries

**Repository/writer:** BFF / same Scheduler subagent. **Reviewer:** fresh implementation reviewer.

**Exact files:**
- modify `package.json`, `pnpm-lock.yaml`
- modify `openapi-ts.scheduler.config.ts`; create `scripts/generate-scheduler-contracts.mjs`
- create only the §4 allow-list under `src/generated/scheduler/`
- delete `src/infrastructure/clients/scheduler/job.ts`
- create `src/infrastructure/clients/scheduler/schedule.ts`, `src/infrastructure/clients/scheduler/control-client.ts`, `src/infrastructure/clients/scheduler/webhook-contract.ts`
- modify `src/infrastructure/clients/scheduler/outbox-delivery.ts`, `src/http/routes/scheduler.ts`
- modify `contract/dependencies/scheduler.json` to `status=generated`
- create `test/scheduler-client.test.ts`
- modify `test/scheduler.test.ts`, `test/scheduled-outbox.test.ts`, `test/scheduled-outbox.integration.mjs`, `test/business-store.integration.mjs`, `test/contract-governance.test.mjs`, `test/architecture.test.ts`
- create `src/application/ports/scheduler-dispatch-receipt-repository.ts`, `src/infrastructure/postgres/scheduler-dispatch-receipt-repository.ts`
- modify `src/application/ports/bff-business-store.ts`, `src/infrastructure/postgres/repositories.ts`, `src/infrastructure/clients/agent/launch.ts`
- create `src/infrastructure/clients/scheduler/dispatch-identity.ts`, `test/scheduler-dispatch-identity.test.ts`, `test/scheduler-dispatch-receipt.integration.mjs`
- update the Scheduler sections of `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/CURRENT.md` to distinguish implemented BFF behavior from unverified cross-owner behavior
- exclude database schema, runtime config, generic public mutation receipt implementation and unrelated routes/docs

**Task 8 design-driven scope clarification (Root):** The current generic receipt reclaims expired pending rows with a new fingerprint and deletes pending bindings on 5xx. Its actor-dependent scope/launch identity cannot satisfy the accepted Scheduler invariants. Use a dedicated Scheduler receipt port/repository over the existing table and existing pool, with an independent protocol scope, immutable digest and launch snapshot, database-time lease and claim-token CAS. No schema, new process, data owner or all-repository layer migration is introduced. The pure identity/canonical JSON algorithm lives in `dispatch-identity.ts`; generated wire/Nano validation stays in `webhook-contract.ts`; SQL remains in the dedicated repository. Do not import generated types into application/domain. The port exposes only local receipt/snapshot values.

- Preserve opaque key bytes and immutable same-key digest across timeout, 5xx and restart; active same-digest pending responds 425; different digest always 409. Stale prepare/finalize/retryable-release must not change newer claims or falsely acknowledge success.
- Freeze the full first-authorized launch snapshot before Agent I/O; retries use the same snapshot. Derive Run identity from an unambiguous tenant/schedule/canonicalNano tuple, not actor or opaque key; ordinary Chat launch identity remains unchanged.
- Use a recursive canonical serializer, not sorted-object reconstruction followed by JSON.stringify. Cover integer-index-looking keys (`"2"`, `"10"`, `"01"`), nested objects, Unicode, arrays, finite numbers, fractional Nano, actor/key/request-id independence and delimiter ambiguity.
- Add real isolated PostgreSQL tests for concurrent claims, different digest after expiry/5xx, stale tokens, snapshot recovery, tenant isolation and response-unknown; wire the new integration file into `test:integration` and the identity test into `test`. No shared fixture cleanup.
- First review repair gate: preserve all original JSON own fields after generated validation (including `__proto__`); reject non-finite JSON numbers with HTTP 400; validate years 0000–0099 without Date.UTC remapping. Add red/green boundary cases.
- Lease correctness uses actual database time after blocking row locks, including claim and fenced mutations. Bound Scheduler Agent I/O by remaining lease minus settlement reserve, independent of a larger global timeout; expired/stale admission must perform no Agent I/O. Real PG lock-wait tests must prove fresh deadlines and fencing.
- Control response hard cap must stop streaming consumption and abort/cancel at the limit, not buffer the entire response before checking.
- Recovery proof requires real PostgreSQL plus HTTP Agent stub: accepted Agent call followed by finalize failure, BFF receiver restart, database task and transport request-ID changes followed by exact first-snapshot resend, and stale prepare preventing Agent I/O. Repository-only tests are not this evidence; align the four docs with actual tests.
- W0B-9 proves BFF/PG behavior; W0B-10 uses real Scheduler/BFF with an Agent receipt stub. True Agent durable admission, parameter conflicts and Agent restart uniqueness remain the W4 Agent-owner closure and do not activate `EDGE-BFF-AGENT` here.

1. Reuse exact generator/Zod pins already installed; add `contract:generate:scheduler` and `contract:check:scheduler` to the aggregate contract gate.
2. RED: old `/jobs`, `job_*`, old header and compact-only time fail; add create/replace/delete 404/409 reconciliation, exact headers, fractional RFC3339, opaque-key replay/conflict, trusted-tenant mismatch, transaction rollback, restart and response-unknown cases.
3. Run focused RED:
   ```bash
   env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm build
   env PATH="$BFF_NODE_BIN:$PATH" corepack pnpm exec node --test test/scheduler-client.test.ts test/scheduler.test.ts test/scheduled-outbox.test.ts test/contract-governance.test.mjs test/architecture.test.ts
   ```
4. Generate both control operations and `webhooks.scheduleOccurrenceDispatch` types/Zod from the vendored artifact. The receiver validates generated header/body/time schemas before application mapping. Replace `/jobs/{name}` with `/schedules/{name}` and delete old names.
5. Run BFF full gate plus:
   ```bash
   ! rg -n '/jobs/|job_not_found|job_already_exists|x-kokoro-scheduler-job|\\^\\\\d\{8\}T' src test contract docs
   git diff --check
   ```
6. Review; commit `fix(bff): align Scheduler control and event contracts`; push; prove remote equality.

### Task 9V: Repair pre-existing AG-UI acceptance fixtures

Root reproduced both failures on unmodified BFF `94a143cc545d74c2d3f518e3cafcc7f0eca0b450` with a separate source snapshot and database (20 pass / 2 fail). This is an independently reviewable test-only slice, not a Scheduler runtime change.

**Exact two files:** `test/agui-http.integration.mjs`, `test/agui-projection.integration.mjs`. The HTTP fixture must register the expected next Run through the existing consumer admission before publishing its source events and must close that owned repository. The projection fixture must supply the existing required requestId to deleteConversation. Keep every frame/cursor/replay/tenant/deletion assertion; no skips, sleeps replacing state synchronization, production changes or shared cleanup. Root owns a separate commit and reruns both suites on isolated PostgreSQL before the final Task9 full gate.

### Task 10: Implement the isolated Scheduler↔BFF smoke runner

**Repository/writer:** Root / Root smoke subagent. **Reviewer:** fresh reliability reviewer.

**Exact files:** create `scripts/e2e/run_scheduler_bff_smoke.py`, `scripts/e2e/scheduler_bff_smoke_runtime.py`, `scripts/e2e/scheduler_bff_smoke_cases.py`, `scripts/tests/test_scheduler_bff_smoke.py`; modify `scripts/INDEX.md`. No gitlink, inventory or control docs.

**Task 10 placement/design gate (Root, 2026-09-22):**

| Item | Decision |
| --- | --- |
| Owner/current facts | Root owns composition verification only. Existing Capability/System runners and Root pytest lifecycle tests are the pattern. BFF `5ea4440941ed65c424fffb0ae834e67b2ae93e74` and Scheduler `975dee59616a1e0eda609aa69283401344900d83` (Task7R2) are clean, pushed prerequisites; Root gitlink lift remains Task11. |
| Responsibility/API | One explicit CLI proves the eleven existing control/receiver cases and returns bounded sanitized JSON evidence; no application API, Schema or owner change. |
| Placement/granularity | Use `scripts/e2e/` plus `scripts/tests/`, matching current Root orchestration; reject a new `verification/e2e/` tree or putting a cross-owner runner in BFF because both duplicate/misplace the current Root responsibility. No new package/framework. |
| Runtime split | Final strengthened draft is runner878/runtime789. Python §12 requires split or an owner/expiry exception above800 lines. Adopt exactly one additional `scheduler_bff_smoke_cases.py` in the same directory for eleven-case behavior and private SQL observation; runner owns CLI/composition lifecycle, runtime owns processes/resources/HTTP fixtures. Reject pushing more code into the nearly800-line runtime or a line-count exception that leaves mixed concerns. Split the long case sequence along control/callback/recovery behavior, not per-line wrappers. No framework/new package; tests import the module owning the behavior. |
| Dependencies/lifecycle | Source-build the exact pinned owners, use their HTTP boundaries; own loopback processes/threads, temporary Go binary/logs, per-owner databases, deadlines and cleanup. No production sibling source import, service restart or blanket Redis cleanup. |
| SQL/data | Apply each canonical schema to a new random database with explicit public search_path. Test harness may inspect/seed only those owned databases; BFF still never queries Scheduler SQL. Capture owner facts rather than simulate Scheduler dispatch. |
| Redis ownership | Use real Redis DB7 for Scheduler and DB8 for BFF. Harness prefix is `kokoro:w0b:scheduler:<run>:`. Scheduler natively hashes `tenant_id + NUL + occurrence_id` to `kokoro:scheduler:dispatch:<sha256>` and has no prefix setting: before deleting databases, derive/register only exact keys from the run's private Scheduler occurrence rows with its nonce tenant, stop all owned processes, then verify/release only this allow-list. Never scan/delete the entire native prefix. This preserves native lease behavior rather than disabling Redis or changing an owner. |
| Proof limits | Positive callback/retry evidence must come from the real Scheduler dispatcher; manual negative requests supplement rather than replace this. An Agent receipt stub records calls and identity only; real Agent durability remains W4. Control conflict/reconciliation must prove the real BFF outbox path. |
| Deletions | No replaced production path in this slice; delete every owned temporary resource on success and failure. Existing Capability runner remains unchanged until Task11. |
| Validation | Focused pytest RED/GREEN, Ruff format/lint, py_compile, actual eleven-case CLI with cleanup assertions, independent Root replay; wrong SHA/version, partial setup, timeout and cleanup failure are nonzero. |


1. Runner CLI is exactly:
   ```bash
   python3 scripts/e2e/run_scheduler_bff_smoke.py \
     --postgres-admin-url "$KOKORO_SMOKE_POSTGRES_URL" \
     --redis-url "$KOKORO_SMOKE_REDIS_URL" \
     --bff-node-bin "$HOME/.nvm/versions/node/v22.22.2/bin" \
     --go-bin "$(command -v go)"
   ```
2. RED unit tests mirror Task 5 lifecycle tests and additionally cover temporary Go binary cleanup, deterministic Agent stub receipt, response-drop proxy and BFF restart. Capture non-zero from `python3 -m pytest scripts/tests/test_scheduler_bff_smoke.py -q`.
3. Create only `w0b_sched_<run>_{scheduler,bff}` databases and prefix `kokoro:w0b:scheduler:<run>:`. Build `./cmd/scheduler` into the runner temp directory with Go 1.26.8; apply both schemas; start real Scheduler and BFF on loopback; start only an owned deterministic Agent receipt stub because `EDGE-BFF-AGENT` is not under activation; wait at most 30 seconds; clean only owned resources.
4. Exactly eleven cases: control create, replace and delete; delete 404 reconciliation; create 409→replace; replace 404→create; fractional RFC3339 callback; duplicate replay; same-key/different-digest 409; trusted header/body tenant mismatch; and one response-unknown scenario that drops the response after durable acceptance, restarts BFF, then retries. Agent stub invocation count remains one per occurrence.
5. GREEN:
   ```bash
   python3 -m pytest scripts/tests/test_scheduler_bff_smoke.py -q
   python3 -m ruff format --check scripts/e2e/run_scheduler_bff_smoke.py scripts/e2e/scheduler_bff_smoke_runtime.py scripts/e2e/scheduler_bff_smoke_cases.py scripts/tests/test_scheduler_bff_smoke.py
   python3 -m ruff check scripts/e2e/run_scheduler_bff_smoke.py scripts/e2e/scheduler_bff_smoke_runtime.py scripts/e2e/scheduler_bff_smoke_cases.py scripts/tests/test_scheduler_bff_smoke.py
   python3 -m py_compile scripts/e2e/run_scheduler_bff_smoke.py scripts/e2e/scheduler_bff_smoke_runtime.py scripts/e2e/scheduler_bff_smoke_cases.py
   # then the exact real CLI above; expected exit 0 and JSON {"status":"PASS","cases":11,...}
   ```
6. Review; commit `test(e2e): add isolated Scheduler BFF smoke`; push.

### Task 10 — Fix Round 1 acceptance

Initial frozen five-file review found four Important and one Minor despite Root focused24/full456/real11case passing. Fix within the same five paths; Root owns control docs/Git. Before changing code, add RED probes for: database/Redis creation applied then acknowledgement lost (retain exact attempted identities, reconcile proved ownership, preserve pre-existing resources, fail closed on unknown query/cleanup); partial HTTP bodies and stalled upstream (bounded accepted sockets, tracked connections/handler threads, bounded shutdown/join); duplicate and restart admitting a second Agent call with the same or a different run ID (bind task/occurrence and entire call snapshots, not only original run count); exact stable Go token (reject 1.26.80/devel/rc/beta and wrong Node/pnpm). Close 191/211-line functions by real lifecycle/control/reconciliation responsibilities; no permanent size exception or new shared framework. Build/start/config composition may move from runtime to runner within these same files to preserve single-purpose modules below800 lines. Repeat final focused, Ruff, compile and real eleven-case CLI before stopping for scoped re-review and Root fresh gates.

### Task 10 — Fix Round 2 acceptance

Fix1 scoped review closes I1/I3/I4/M1 but retains slow upstream-body shutdown (F1) and finds unapproved automatic RFC1918 callback binding (F2). Root has not approved widening the loopback boundary; no user choice has arrived. Same five-file writer only. F1: enforce a whole-operation monotonic deadline and register/cancel outbound response/socket before bounded handler joins; add a loopback upstream that sends headers then trickles bytes faster than idle timeout, and prove fixture exits without test-side upstream closure or remaining threads. Preserve partial-body/stalled-upstream tests. F2: remove RFC1918 auto-binding; callback/listener accepts only loopback, prefer loopback among multiple DNS answers, and reject private-only DNS before service/database setup where practical. Add private-only rejection and mixed-address loopback tests. Do not edit hosts/resolver/shared network config, install DNS machinery, relax Scheduler target policy, or claim a non-loopback CLI as accepted. If current hostname remains non-loopback, report the exact real CLI environment failure, stop and hand off reviewed code without claiming Task10 acceptance. A later explicit user network-boundary choice requires a separate recorded decision and inbound peer checks, not silent scope expansion. Keep files/functions within the approved responsibility gates; if a genuinely needed new file arises, report before adding it.

### Task 10 — Fix Round 3 acceptance and HTTP placement gate

Fix2 is frozen against Root `f44f8175089c0658962e352bd8a493a9c293aad9`: Root focused47/full479 passed, but the independent reviewer retains one Important. A loopback upstream sending an unfinished header one byte every100ms keeps `getresponse()` alive after4.3s despite the declared3s operation deadline. F2 loopback/fail-closed is closed; the real CLI currently exits1 before resource creation because the hostname resolves only to192.168.1.4. Do not weaken this boundary or count the environment failure as a code acceptance.

Original writer receives Fix Round3. The same deadline must actively interrupt all request/status/headers/body I/O, not only be checked after a blocking operation. Track the actually owned socket even when HTTP/1.0 transfers it away from `connection.sock`; a cancellation guard must handle late socket registration and cancel/join its own timer on every exit. Numeric loopback upstream validation may bound DNS assumptions, but no owner target-policy or network-configuration change is permitted. Tests must keep the upstream alive while status/headers trickle past the deadline and prove the operation independently fails, then check all owned threads/connections are gone. Keep existing body/idle/partial-input/cancellation cases and resource ownership regressions.

| Placement item | Root decision before creating files |
| --- | --- |
| Owner/current facts | Root composition HTTP fixtures only; runtime774 lines currently mixes process/SQL/Redis lifecycle with Agent stub/proxy HTTP. Main test798 lines mixes resource/toolchain and socket tests. The original writer remains the sole source writer; Root owns controls/Git. |
| Responsibility and location comparison | Adopt `scripts/e2e/scheduler_bff_smoke_http.py` for existing owned HTTP server, Agent receipt stub, response-drop proxy and operation cancellation. Reject adding another HTTP abstraction to the near-limit runtime or a cross-runner common framework. Tests belong in `scripts/tests/test_scheduler_bff_smoke_http.py`, not in either child owner. |
| Granularity/dependencies | Move the existing cohesive HTTP block and its socket tests, not arbitrary lines. Runtime retains process/DB/Redis ownership and SmokeError; HTTP may import that error, runtime must not import HTTP. Runner/cases/tests import HTTP symbols directly from their new owner; delete old definitions/import aliases. No new directory, service or public API. |
| Data/API/deletions | No SQL, production contract, owner release or Agent semantics change. Move definitions once without compatibility re-exports; maintain eleven cases, strict loopback and exact immutable owner pins. |
| Exact scope/verification | Previous five paths plus the two HTTP files (seven total). Record movement separately from F1 logic in the review package. RED/GREEN for slow status/headers and deadline cleanup; both focused test files, all Root pytest, Ruff/compile for all Python slice files; real CLI result and exact cleanup, independent scoped review. No file>800/function>100 without a new explicit decision. |

### Task 5R: Repair Capability smoke resource and HTTP lifecycle parity

Task10 reviewer read-only confirmed the same CREATE failure path in the already accepted Capability runner. This known defect must close before Task11 activation, not be hidden by a normal-path smoke.

**Owner/writer:** Root smoke subagent, dispatched only after Task10 acceptance. **Exact files:** `scripts/e2e/run_capability_bff_smoke.py`, `scripts/tests/test_capability_bff_smoke.py`. Preserve tests/fixtures already accepted; no child, contract, inventory or gitlink change. Port only the reviewed resource ownership/acknowledgement-loss behavior needed by this runner, with RED/GREEN for uncertain CREATE/SET, before-create failure, pre-existing resource preservation and cleanup-query errors. Root also independently reproduced its readiness fixture retaining one handler after a partial-header client and context exit; apply the same bounded owned-HTTP lifecycle fix and assert no leftover handler, without shared-infrastructure access. No new cross-runner common framework. Advance BFF runtime input to accepted `5ea4440941ed65c424fffb0ae834e67b2ae93e74`, preserving precise wrong-SHA rejection, so real validation uses the available pushed child. Root reruns tests and the exact eight-case CLI before independent two-file commit. Task11 then integrates the new composition and does not duplicate this completed pin repair.

### Task 11: Integrate Scheduler and activate two edges

**Repository/writer:** Root / Root integration subagent. **Reviewer:** cross-repository reviewer.

**Exact files:** modify gitlink `apps/kokoro-bff`; Scheduler gitlink only if Task 7 produced a separate pushed owner commit; modify `verification/contracts/consumer-inventory.json`, `docs/task.md`, `docs/progress.md`, `scripts/e2e/run_capability_bff_smoke.py` and its `scripts/tests/test_capability_bff_smoke.py` regression coverage; update `scripts/tests/test_contract_compatibility.py` for the Task7R2 Scheduler runtime release pin.

1. Lift pushed child SHA(s) and refresh every fan-out reference/digest. Advance the existing Capability smoke BFF release input to the accepted consumer SHA; preserve exact-SHA rejection and run its unit gate plus real smoke against the new combination.
2. `EDGE-BFF-SCHEDULER`: pin BFF generated control/npm generator/BFF `.node-version`. `EDGE-SCHEDULER-BFF`: pin BFF generated webhook validator/route/test/npm generator/BFF `.node-version`; add Scheduler `go.mod` producer assertion. Both pin Scheduler owner blob. Keep `EDGE-SCHEDULER-AGENT` broken.
3. Run Task 10 real CLI, Root topology/tests/ten-repository audit, and `python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-exit.json`; non-debt gates exit `0`.
4. Review; commit `fix(integration): activate Scheduler BFF contract edges`; push; require clean Root.

---

## Chunk 4 — Delete dead Storage HTTP and freeze W1/W2 handoff

### Task 12: Freeze BFF Storage degraded behavior

**Repository/writer:** BFF / BFF Storage design subagent. **Reviewer:** architecture reviewer.

**Exact files:** modify `docs/TECHNICAL_DESIGN.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/CURRENT.md`, `docs/api/v1/library.md`, `docs/api/v1/README.md`, `test/contract-governance.test.mjs`, `test/architecture.test.ts`. No Root file, runtime source, package/lock or schema.

1. RED docs/architecture tests require the old URL/config to be non-canonical, Storage v2 as sole target, exact W1/W2 owners and fail-closed interim behavior.
2. Freeze `GET /v1/library` as `503 storage_integration_unavailable`; no upstream connection. Record W2 prerequisites: Storage default-deny caller×operation×scope matrix; Capability scope mapping; Agent trusted Run/ExecutionIdentity mapping; BFF Wave 1 IAM admission; per-kind or BFF composite pagination decision.
3. Run BFF build, focused governance/architecture tests, contract check and `git diff --check` with exact BFF PATH form.
4. Review; commit `docs(bff): freeze Storage v2 handoff`; push.

### Task 13: Record the Root W1/W2 Storage handoff

**Repository/writer:** Root / Root controller. **Reviewer:** Root architecture reviewer. **Start:** Task 12 remote SHA.

**Exact files:** modify `docs/task.md`, `docs/progress.md`. No plan edit, gitlink, inventory or child file.

1. Copy the five Task 12 prerequisites into W1/W2 acceptance criteria and record the BFF docs SHA.
2. Run Root topology/tests and `git diff --check`; all exit `0`.
3. Review; commit `docs(governance): bind Storage authorization handoff`; push.

### Task 14: Delete BFF `/internal/bff/library`

**Repository/writer:** BFF / same Storage subagent. **Reviewer:** fresh implementation reviewer.

**Exact files:** modify `src/http/routes/owner.ts`, `src/application/projections.ts`, `src/config/runtime.ts`, `test/bff.test.ts`, `test/config.test.ts`, `test/architecture.test.ts`, `test/contract-governance.test.mjs`, `docs/api/v1/library.md`, `docs/api/v1/README.md`. No schema, package/lock or generated file.

1. RED: `/v1/library` opens no socket and returns the stable 503 envelope; old URL and `KOKORO_STORAGE_BASE_URL` fail architecture/config tests.
2. Delete the runtime call, `libraryData`, Storage HTTP upstream config and stale tests/docs. Preserve the public endpoint only as the explicit fail-closed W2 placeholder.
3. Run BFF full gate and:
   ```bash
   ! rg -n 'internal/bff/library|KOKORO_STORAGE_BASE_URL|libraryData' src test contract docs
   git diff --check
   ```
4. Review; commit `fix(bff): remove dead Storage HTTP integration`; push; prove remote equality.

### Task 15: Integrate the Storage deletion without activating Storage

**Repository/writer:** Root / Root integration subagent. **Reviewer:** cross-repository reviewer.

**Exact files:** modify gitlink `apps/kokoro-bff`, `verification/contracts/consumer-inventory.json`, `docs/task.md`, `docs/progress.md`, both `scripts/e2e/run_capability_bff_smoke.py` and `scripts/e2e/run_scheduler_bff_smoke.py`, and `scripts/tests/test_capability_bff_smoke.py` and `scripts/tests/test_scheduler_bff_smoke.py`.

1. Lift Task 14 BFF SHA and refresh all BFF fan-out commits/digests, including both smoke runners' BFF release inputs. Keep wrong-SHA rejection and verify the two runner unit suites before their real smoke gates.
2. Keep `EDGE-BFF-STORAGE` broken; update its reason/evidence to the explicit W1/W2 dependency. No Storage state or owner pin changes.
3. Run Root full gate with `w0b-exit`; compatibility IDs must remain exactly unchanged. Re-run both real smoke CLIs.
4. Review; commit `fix(integration): remove dead BFF Storage HTTP path`; push; require clean Root.

---

## Chunk 5 — Whole-wave freeze

### Task 16: Final W0B review and evidence freeze

**Repository/writer:** Root / Root controller. **Reviewers:** independent specification and quality agents bound to one frozen SHA.

**Exact files:** modify `docs/task.md`, `docs/progress.md`, `docs/INDEX.md`. Review findings require a new scoped task; reviewers do not edit.

1. Generate the review package from `bfa054f3` through current HEAD with every child baseline/delivery/integrated/remote SHA and no unreviewed fix.
2. SPEC checks owner-first order, temporary Capability ownership, Scheduler producer-owned event, receiver consumer evidence, Storage deferral and exact ID transitions. QUALITY checks generation drift, provenance, remote reachability, fan-out refresh, identity trust, timeout/cancel, idempotency/recovery and owned-resource cleanup.
3. Run both real smoke CLIs; Root full gate with `w0b-exit`; every touched child full gate; `git diff --check`. Record exact exits/counts and any honest ten-repository debt.
4. Require both reviews `✅` with `0/0/0`. Update task/progress/INDEX, commit `docs(governance): freeze wave 0b evidence`, push.
5. Verify Root and touched children are clean, on sole `main`, and local main equals remote. Only then draft the Wave 1 IAM plan; Goal remains active.
