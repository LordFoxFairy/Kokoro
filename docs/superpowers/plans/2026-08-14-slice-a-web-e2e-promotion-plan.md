# Slice A Backend E2E, Web Adapter and Atomic Promotion Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before a lane starts, its next milestone MUST be expanded into a separately reviewed JIT implementation cut with exact files, actual RED test/code, self-contained commands and one precise commit; workers never invent omitted code from this roadmap.

**Goal:** Prove the complete SQL-backed SiteContext → IAM → Chat → Agent → HITL → restart/replay backend chain without a browser, then connect the mature User Web through thin generated adapters and atomically promote the reviewed repositories.

**Architecture:** Root first runs native local PostgreSQL, Redis, LiteLLM, IAM, Model, Capability, Chat and Agent and drives them through generated service clients; User Web is absent from this backend acceptance gate. The backend harness selects the same allowlisted Host → SiteContext fixture that Web/BFF later loads from server environment, while IAM independently validates the selected active Site/Organization/session facts in PostgreSQL. After that gate passes, browser traffic remains same-origin HTTP/SSE through the User BFF, which uses generated owner clients and preserves the existing reducer/machine. Root owns repeatable PG18 E2E, exact candidate pins and the final release inventory. `kokoro-platform` remains pinned but dormant as the Slice B/C migration source; `kokoro-session` is replaced by `kokoro-chat` only after both backend and browser gates pass.

**Tech Stack:** Native PostgreSQL 18, Redis, LiteLLM, Python 3.11 process orchestration and gRPC/HTTP E2E clients, repository-local pnpm/uv dev entries, Next.js User app, TypeScript, generated Connect clients, Zod, Vitest and Playwright.

## Global Constraints

- Root composition/E2E changes stay in the Root worktree until the final atomic commit. Web changes work only in `/tmp/kokoro-web-slice-a`, created from `kokoro-web@f3936befb7ae4c219273ae9b7f4efb97cb6a1425`, and the exact frozen Root contract commit. Do not edit the canonical Web submodule checkout.
- Preserve existing Web reducer, machine, SSE reconnect, idempotency, HITL, sealed session envelope and mobile UI. Change adapters, not state semantics.
- Browser never receives IAM, Chat or Agent service credentials and never calls service RPC directly.
- Web's server-only clients use the mounted Web workload token to call IAM 7202 and Chat 7205; the BFF also forwards only the IAM access JWT recovered from its sealed httpOnly envelope.
- Web/BFF normalizes the request Host and resolves it only through `KOKORO_SITE_CONTEXTS_JSON`, a server-only exact-host map whose values include the Site ID and shell-owned brand/skin configuration. Unknown or ambiguous Hosts fail closed. Browser-supplied `site_id` and untrusted forwarding headers never select SiteContext.
- The exact runtime child allowlist is IAM, Model, Capability, Chat, Agent and Web. Frozen compatibility-artifact retirement is defined only by the structured retirement boundary in the master roadmap.
- Snapshot hydration must include complete messages/parts, active run, active interaction and watermark; bounded stream retention must not erase conversation history.
- No `kokoro-platform` API, Hub, Mongo, MySQL, Storage, Entitlement or Payment process participates in Slice A E2E.
- The backend service E2E must pass before any Web adapter task begins. Root pin/release changes are one final commit after all candidate repositories are clean, reviewed and reproducible from exact commits.

---

### Milestone 1: Add the Root native local-dev Slice A orchestration

**Files:**
- Create: `scripts/slice_a/native.py`, `wait_ready.py`, `seed.py`, `create_secrets.py`, `create_fixture_dir.py`, `cleanup.py`, `promote.py`, `__init__.py`
- Create: `scripts/fixtures/openai_slice_a.py`, `scripts/tests/test_openai_slice_a_fixture.py`
- Create: `scripts/tests/test_slice_a_native.py`
- Modify: `scripts/INDEX.md`, `scripts/verify-all.py`

**Interfaces:**
- Consumes: clean IAM, Model, Capability, Chat and Agent candidate commits, their native `pnpm dev`/`uv run` entries, committed Root baseline/contracts and the reviewed SiteContext fixture.
- Produces: a browser-independent native backend lifecycle and an optional `--with-web` lifecycle used only after Milestone 2 passes.

**JIT cut requirement 1 — Write a failing native process-inventory test**

`test_slice_a_native.py` starts the orchestrator with a temporary state directory and asserts this exact
backend process set:

```python
BACKEND_PROCESSES = {
    "postgres", "redis", "model-fixture", "litellm",
    "iam", "model", "capability", "chat", "agent",
}
OPTIONAL_WEB_PROCESS = "user-web"
```

The test must prove:

- PostgreSQL 18 is initialized in a fresh local data directory and receives only the committed Root baseline;
- every owner is launched from its explicit candidate path through its repository-native development entry;
- `user-web` is absent from the backend gate and appears only with `--with-web`;
- no Platform, Session, MySQL or Mongo process, URL or environment variable is present;
- the state file records exact PID, process-start identity, argv, cwd, port and readiness endpoint for every child;
- shutdown terminates only the recorded process groups, waits for exit and proves every owned port is returned;
- stale PID reuse, an occupied port, a pre-existing state directory or a failed readiness check fails loudly;
- promotion input rejects branch names, missing remote commit objects and tree-digest mismatches.

The same RED test creates a temporary secret directory and asserts `create_secrets.py` writes the exact
controlled manifest: `web.workload-token`, `chat.workload-token`, `agent.workload-token`,
`iam.refresh-derivation-key`, `web.session-key`, `litellm.api-key` as independent random
32-byte/64-lowercase-hex files mode `0600`; plus `iam.jwt-private.pem` mode `0600` and its matching
`iam.jwt-public.pem` mode `0644`. Re-running with a symlink, wrong mode, mismatched keypair or unexpected
ninth file fails closed. `cleanup.py` removes only an explicitly supplied marked state/secret/fixture directory
and refuses `/`, an empty path or a directory without its generated marker.

User Web receives `web.session-key` only through `KOKORO_WEB_SESSION_KEY_FILE`; its adapter reads the file
once, uses the bytes for the existing session envelope and derives the magic-state HKDF subkey. The production
config removes the direct `KOKORO_WEB_SESSION_SECRET` value path so there is one name and one file authority.

`create_fixture_dir.py` creates a separately marked mode-0700 directory with one empty `magic-links/` child.
Only IAM receives write access while `KOKORO_RUNTIME_MODE=fixture`; no other process may write it. Tests accept
only an already-created, empty, caller-owned, non-symlink directory and reject non-empty/already-marked/wrong-
owner/wrong-mode paths.

**JIT cut requirement 2 — Implement the native lifecycle**

- `native.py start --fresh` locates the local PostgreSQL 18 binaries, initializes an isolated cluster/database,
  starts local Redis and the deterministic OpenAI fixture, then starts LiteLLM and each owner through its native
  dev command. Missing binaries or a version other than PostgreSQL 18 fail before any child starts.
- The exact repository commands are IAM/Model/Capability `pnpm dev`, Chat `npm run dev`, Agent
  `uv run kokoro-agent-local --dev`, and—with `--with-web` only—User Web's workspace-local `pnpm dev`.
  The orchestrator does not replace these commands with built artifacts, in-process adapters or test doubles.
- Root applies `database/baseline/kokoro.sql` before owner readiness. `seed.py` provisions the bounded local Site
  fixture and invokes owner bootstrap entrypoints; application services never become schema migration writers.
- Candidate roots are explicit parameters (`--iam /tmp/kokoro-iam-slice-a`, etc.); there is no implicit sibling
  checkout or branch lookup.
- Secrets are read from the controlled file manifest and passed only to the minimum process. No value appears in
  argv, logs, evidence JSON or Git.
- Agent calls real local LiteLLM on 4000 with the mounted key. The deterministic fixture maps only
  `slice-a-fixture`; production provider configuration is outside this test lifecycle and may not silently fall
  back to the fixture.
- IAM receives the fixture delivery directory only in the test lifecycle. Its atomic file semantics remain the
  owner repository's responsibility; Root reads the caller-known request file once and deletes it.
- Health/readiness proves each process's database/RPC dependencies without impersonating a user.
- `native.py restart agent|chat` stops the recorded process group, proves the port is free, starts the exact same
  candidate command and waits for readiness. This is the required recovery path, not an in-process adapter swap.

`openai_slice_a.py` is a test-only OpenAI Chat Completions server. For the first request containing user text
`slice-a-hitl`, its streaming response contains exactly one `request_human` tool call with stable ID
`call_slice_a_approval`, JSON arguments `{"kind":"approval","prompt":"Approve Slice A?"}`,
`finish_reason="tool_calls"` and usage `{prompt_tokens:11, completion_tokens:7, total_tokens:18}`. When the
request history contains that tool result, it streams `Slice A approved.` with usage
`{prompt_tokens:19, completion_tokens:4, total_tokens:23}`. Any other model/prompt returns 400. The fixture test
sends both requests directly, then through real local LiteLLM, and asserts identical tool-call/content/usage facts
reach the Agent-compatible OpenAI client.

**JIT cut requirement 3 — Run the native lifecycle gate**

```bash
set -euo pipefail
uv run --frozen pytest scripts/tests/test_slice_a_native.py scripts/tests/test_openai_slice_a_fixture.py -q
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-fixtures.XXXXXX)"
STATE_PARENT="$(mktemp -d /tmp/kokoro-slice-a-state-parent.XXXXXX)"
STATE_DIR="$STATE_PARENT/state"
export KOKORO_SLICE_A_STATE_DIR="$STATE_DIR"
cleanup_native() {
  if test -e "$STATE_DIR"; then
    uv run --frozen python scripts/slice_a/native.py stop --state-dir "$STATE_DIR" || true
    uv run --frozen python scripts/slice_a/cleanup.py --dir "$STATE_DIR" || true
  fi
  test ! -e "$KOKORO_SLICE_A_SECRET_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  test ! -e "$KOKORO_SLICE_A_FIXTURE_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
  rm -rf -- "$STATE_PARENT"
}
trap cleanup_native EXIT INT TERM
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
uv run --frozen python scripts/slice_a/native.py start --fresh \
  --state-dir "$KOKORO_SLICE_A_STATE_DIR" \
  --secret-dir "$KOKORO_SLICE_A_SECRET_DIR" \
  --fixture-dir "$KOKORO_SLICE_A_FIXTURE_DIR" \
  --iam /tmp/kokoro-iam-slice-a \
  --model /tmp/kokoro-model-slice-a \
  --capability /tmp/kokoro-capability-slice-a \
  --chat /tmp/kokoro-chat-slice-a \
  --agent /tmp/kokoro-agent-slice-a
uv run --frozen python scripts/slice_a/wait_ready.py --state-dir "$KOKORO_SLICE_A_STATE_DIR"
cleanup_native
trap - EXIT INT TERM
git diff --check -- scripts/slice_a scripts/fixtures scripts/tests scripts/verify-all.py scripts/INDEX.md
```

These Root files remain uncommitted until atomic promotion. Any native lifecycle RED blocks backend freeze; no
packaging work may substitute for this gate.

### Milestone 2: Prove the real backend chain and restart invariants

**Files:**
- Create: `scripts/e2e/generated/**` from the frozen Root contracts
- Create: `scripts/e2e/slice_a_backend.py`, `scripts/e2e/test_slice_a_backend.py`
- Modify: `scripts/verify-all.py`

**Interfaces:**
- Consumes: the Task 1 backend profile, reviewed Host → SiteContext fixture and exact generated IAM/Chat clients; downstream Agent/Capability/Model behavior is observed only through Chat product APIs.
- Produces: the first release-blocking Slice A milestone, independent of Browser and Web code.

**JIT cut requirement 1 — Write RED backend assertions before orchestration**

The pytest fixture must call real product service endpoints and fail if any owner is replaced by an in-process fake. It authenticates as the Web workload only and reaches downstream Agent/Capability/Model exclusively through Chat; it never loads Chat/Agent workload secrets or calls their private RPCs directly. Wrong-token private-boundary checks live in each owner repository and the native process security suite. It performs exactly:

1. Apply the committed Root baseline to a fresh PostgreSQL 18 database, provision the bounded local Site fixture (`site_site` plus its exact host binding) and invoke Model's owner-only versioned bootstrap command. Assert exact replay succeeds, drift fails, and no runtime service other than IAM accesses Site rows.
2. Resolve the normalized test Host through the same server-only SiteContext fixture format used by Web/BFF; assert an unknown Host fails and the selected `site_id` matches the provisioned active Site.
3. Call IAM `RequestMagicLink` with that trusted Web workload/SiteContext, read the local fixture mailer's token, then `ConsumeMagicLink`; assert Principal, personal Organization, owner Membership, role bindings and all five Slice A permissions. Suspend the Site and assert IAM rejects the same binding before restoring it.
4. Call Chat `CreateConversation`, then authorize and `SubmitMessage` with caller-generated command IDs.
5. Observe Agent claim, empty Capability snapshot resolution, Model selection and the existing deterministic LiteLLM/GA execution path.
6. Read Chat snapshot and SSE tail; assert user/assistant messages, run view and a deterministic HITL request.
7. Call Chat `DecideInteraction`; assert Agent control receipt, resume and exactly one terminal projection.
8. Stop Agent after a durable event commit, restart it, and assert outbox replay creates no duplicate event/effect. Stop and restart Chat and assert the same complete snapshot.
9. Run the production retention cycle, request an expired cursor and assert typed `SNAPSHOT_REQUIRED`; refetch snapshot at its watermark and observe the new tail without history loss.
10. Replay each mutating command with the same digest, then with a changed digest; assert stable result followed by conflict.

**JIT cut requirement 2 — Verify the committed Root-owned test clients and provenance**

```bash
ROOT_CURRENT="$(git rev-parse --show-toplevel)"
ROOT_CONTRACT_COMMIT="$(python3 -c 'import json; print(json.load(open("scripts/e2e/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"
CONTRACT_WORKTREE_PARENT="$(mktemp -d /tmp/kokoro-contract-source.XXXXXX)"
CONTRACT_WORKTREE="$CONTRACT_WORKTREE_PARENT/root"
git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"
trap 'git worktree remove --force "$CONTRACT_WORKTREE" 2>/dev/null || true; rm -rf "$CONTRACT_WORKTREE_PARENT"' EXIT
(cd "$CONTRACT_WORKTREE" && pnpm install --frozen-lockfile && uv sync --frozen --group dev)
(cd "$CONTRACT_WORKTREE" && uv run --frozen python contract/generate.py --source-root "$CONTRACT_WORKTREE" --source-commit "$ROOT_CONTRACT_COMMIT" --consumer root-e2e --repo "$ROOT_CURRENT" --check)
git worktree remove --force "$CONTRACT_WORKTREE"
rm -rf "$CONTRACT_WORKTREE_PARENT"
trap - EXIT
```

The generated Python clients were committed by the Root contract plan as a descendant output commit and are test harness code only; services still use their own generated consumers. The provenance file must pin the same Root contract commit and source digest used by every child.

**JIT cut requirement 3 — Run twice from fresh state with no Web process**

```bash
run_backend_once() (
  set -euo pipefail
  label="$1"
  STATE_PARENT="$(mktemp -d "/tmp/kokoro-slice-a-${label}-state-parent.XXXXXX")"
  STATE_DIR="$STATE_PARENT/state"
  secret_dir="$(mktemp -d "/tmp/kokoro-slice-a-${label}-secrets.XXXXXX")"
  fixture_dir="$(mktemp -d "/tmp/kokoro-slice-a-${label}-fixtures.XXXXXX")"
  cleanup_native() {
    if test -e "$STATE_DIR"; then
      uv run --frozen python scripts/slice_a/native.py stop --state-dir "$STATE_DIR" || true
      uv run --frozen python scripts/slice_a/cleanup.py --dir "$STATE_DIR" || true
    fi
    test ! -e "$secret_dir" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$secret_dir" || true
    test ! -e "$fixture_dir" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$fixture_dir" || true
    rm -rf -- "$STATE_PARENT"
  }
  trap cleanup_native EXIT INT TERM
  uv run --frozen python scripts/slice_a/create_secrets.py --dir "$secret_dir"
  uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$fixture_dir"
  uv run --frozen python scripts/slice_a/native.py start --fresh \
    --state-dir "$STATE_DIR" --secret-dir "$secret_dir" --fixture-dir "$fixture_dir" \
    --iam /tmp/kokoro-iam-slice-a --model /tmp/kokoro-model-slice-a \
    --capability /tmp/kokoro-capability-slice-a --chat /tmp/kokoro-chat-slice-a \
    --agent /tmp/kokoro-agent-slice-a
  KOKORO_SLICE_A_STATE_DIR="$STATE_DIR" \
  KOKORO_SLICE_A_EVIDENCE_PATH="/tmp/kokoro-slice-a-${label}.json" \
    uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
  uv run --frozen python scripts/slice_a/native.py assert-no-process --state-dir "$STATE_DIR" --name user-web
  cleanup_native
  trap - EXIT INT TERM
)
run_backend_once first
run_backend_once second
uv run --frozen python scripts/e2e/slice_a_backend.py compare-evidence \
  /tmp/kokoro-slice-a-first.json /tmp/kokoro-slice-a-second.json
```

Each `start --fresh` initializes a distinct local PostgreSQL 18 cluster, applies the committed baseline and
starts fresh repository-native processes. The two runs must produce the same baseline digest, PostgreSQL catalog
inventory and seed result: exactly 50 owner tables plus four checkpointer tables and no unexpected business
uniqueness. Both runs exercise real OS-process Agent and Chat restarts through `native.py restart`; no process or
port may remain after cleanup.

**JIT cut requirement 4 — Freeze the backend milestone**

```bash
uv run --frozen python scripts/verify-all.py --slice-a-backend
git diff --check -- scripts/e2e scripts/verify-all.py
```

Any backend RED stops execution here. Do not begin Task 3 and do not use a Web mock to bypass it. Root E2E files remain uncommitted until Task 9 because they depend on candidate gitlinks/build contexts.

### Milestone 3: Generate IAM and Chat clients for the User BFF

**Files:**
- Create: `kokoro-web/apps/user/src/generated/iam/**`, `chat/**`, `http/**`
- Create: `kokoro-web/apps/user/src/lib/server/site-context.ts`, `iam-client.ts`, `chat-client.ts`, `service-identity.ts`
- Modify in `/tmp/kokoro-web-slice-a`: `apps/user/package.json`, `pnpm-lock.yaml`, `apps/user/src/lib/server/INDEX.md`
- Test: `kokoro-web/apps/user/src/lib/server/__tests__/service-clients.test.ts`

**JIT cut requirement 1 — Verify the Root-generated consumer closure, then write the failing server-client test**

```bash
ROOT_CONTRACT_COMMIT="$(python3 -c 'import json; print(json.load(open("scripts/e2e/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"
CONTRACT_WORKTREE_PARENT="$(mktemp -d /tmp/kokoro-contract-source.XXXXXX)"
CONTRACT_WORKTREE="$CONTRACT_WORKTREE_PARENT/root"
git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"
trap 'git worktree remove --force "$CONTRACT_WORKTREE" 2>/dev/null || true; rm -rf "$CONTRACT_WORKTREE_PARENT"' EXIT
(cd "$CONTRACT_WORKTREE" && pnpm install --frozen-lockfile && uv sync --frozen --group dev)
(cd "$CONTRACT_WORKTREE" && uv run --frozen python contract/generate.py --source-root "$CONTRACT_WORKTREE" --source-commit "$ROOT_CONTRACT_COMMIT" --consumer kokoro-web --repo /tmp/kokoro-web-slice-a --check)
git worktree remove --force "$CONTRACT_WORKTREE"
rm -rf "$CONTRACT_WORKTREE_PARENT"
trap - EXIT
```

Expected: generation check is green because the Root lane produced the candidate outputs. Then add `service-clients.test.ts`; it must fail because the server-only client factory is absent.

**JIT cut requirement 2 — Install the exact generated-client runtime dependencies**

Generated provenance must include the source commit, source tree digest, plugin versions and every output digest. Install the exact server-only dependencies and update the existing lockfile from the Web Git root:

```bash
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user add --save-exact \
  @connectrpc/connect@2.1.2 @connectrpc/connect-node@2.1.2 @bufbuild/protobuf@2.14.0)
```

Do not hand-edit generated files or import the clients into browser components.

**JIT cut requirement 3 — Add server-only client factories**

```ts
export interface UserBackendClients {
  iam: IamAuthenticationServiceClient
  chatCommands: ChatCommandServiceClient
  chatQueries: ChatQueryServiceClient
}

export function createUserBackendClients(env: NodeJS.ProcessEnv): UserBackendClients
```

Read service endpoints and credentials only from server environment. `site-context.ts` validates `KOKORO_SITE_CONTEXTS_JSON` at startup, canonicalizes each exact Host once and returns a frozen SiteContext without network I/O. Reject browser bundles that import either factory through an architecture test. Production imports are limited to the exact IAM/Chat generated surface.

**JIT cut requirement 4 — Verify and commit in `kokoro-web`**

```bash
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user test -- service-clients)
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user typecheck)
git -C /tmp/kokoro-web-slice-a add apps/user/src/generated apps/user/src/lib/server apps/user/package.json pnpm-lock.yaml
git -C /tmp/kokoro-web-slice-a commit -m "chore(web): consume Slice A IAM and Chat clients"
```

### Milestone 4: Rebind authentication to IAM without Chat bootstrap

**Files:**
- Modify in `/tmp/kokoro-web-slice-a`: `apps/user/src/app/api/auth/**`, `src/lib/server/auth.ts`, `session-envelope.ts`, `site.ts`
- Test: `kokoro-web/apps/user/src/lib/server/__tests__/iam-auth.test.ts`

**Interfaces:**
- Consumes Web's server-side SiteContext binding and IAM generated clients.
- Produces the existing sealed browser auth session containing only IAM identity/session context; it does not create a Project or Conversation during login.

**JIT cut requirement 1 — Write RED tests**

- Mock IAM login returning access/refresh tokens; assert the BFF response and browser storage omit both while the httpOnly sealed cookie decrypts to them server-side.
- Rotate once, replay the old refresh token and assert the envelope is cleared plus IAM's family-replay error is preserved.
- Complete login and assert the envelope contains principal/Site/organization/auth-session context, while Chat receives zero calls.
- Configure two exact Host bindings with different Site IDs/skins; assert each Host selects only its own frozen SiteContext, unknown/duplicate/case-conflicting Hosts fail closed, and a browser `site_id` cannot override selection.
- Send forged principal/Site/organization headers and assert the BFF forwards only values recovered from the envelope.

**JIT cut requirement 2 — Replace only the backend adapter**

Keep the current httpOnly AES-GCM envelope and Origin/CSRF fences. Replace `AuthConfig` legacy `userBaseUrl/sessionBaseUrl/siteId/hubBaseUrl/paymentBaseUrl` with exact IAM/Chat endpoints, workload credential and the validated server-only Host → SiteContext binding. `site.ts` normalizes the request Host and resolves it locally from that immutable allowlist before `RequestMagicLink`; there is no external resolution adapter or browser-controlled fallback.

Map IAM `RequestMagicLink/ConsumeMagicLink/RefreshSession/Logout/GetSession` into the existing routes and envelope. The Slice A envelope contains exactly `principalId`, `siteId`, `organizationId`, `authSessionId`, `accessToken`, and `refreshToken`. It contains no Project, Conversation or Agent namespace; those are Chat-owned results created only when the user starts a conversation. Remove old User/Team namespace semantics.

Team, Hub, Billing and Shared routes are explicit Slice A feature-off responses and their modules/config paths must not read legacy endpoints. Their UI entry points render unavailable state; they are not silently proxied to dormant Platform services.

The hard-cut covers the concrete route trees `apps/user/src/app/api/team/**`, `api/hub/**`, `api/billing/**` and `api/shared/**`. Add `apps/user/src/app/api/__tests__/slice-a-feature-off-routes.test.ts`: load every route module, assert its declared feature-off response, and instrument `fetch` plus legacy config accessors to prove zero calls. This is a temporary Slice A product decision, not a catch-all proxy.

The same focused Slice A UI gate disables controls whose owner APIs are intentionally absent: rename/delete Conversation, artifact/library actions, explicit cancel and streaming submit/steer. A disabled streaming composer cannot append a ghost user bubble before receiving `CONVERSATION_RUN_ACTIVE`. These controls return only when their exact owner RPCs enter a later reviewed slice; no button may call a legacy endpoint.

**JIT cut requirement 3 — Verify and commit**

```bash
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user test -- iam-auth)
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user typecheck)
git -C /tmp/kokoro-web-slice-a add \
  apps/user/src/app/api/auth apps/user/src/lib/server \
  apps/user/src/app/api/team apps/user/src/app/api/hub apps/user/src/app/api/billing apps/user/src/app/api/shared \
  apps/user/src/app/api/__tests__/slice-a-feature-off-routes.test.ts
git -C /tmp/kokoro-web-slice-a commit -m "refactor(web): use IAM session authority"
```

### Milestone 5: Rebind session commands and query paths to Chat RPC

**Files:**
- Modify: `kokoro-web/apps/user/src/app/api/session/[...path]/route.ts`, `src/engine/client.ts`, `src/engine/config.ts`
- Create: `kokoro-web/apps/user/src/lib/server/chat-bff.ts`
- Test: `kokoro-web/apps/user/src/lib/server/__tests__/chat-bff.test.ts`, `apps/user/src/engine/__tests__/client.test.ts`
- Test: `kokoro-web/apps/user/src/app/api/__tests__/slice-a-openapi-parity.test.ts`

**JIT cut requirement 1 — Lock the HTTP-to-RPC mapping in RED tests**

The BFF maps create conversation, submit, control, recover, list conversations and snapshot reads to exact Chat RPC methods. The browser SSE handler calls generated server-streaming `ChatQueryService.StreamConversationEvents`, forwards `Last-Event-ID` as `after_seq`, validates each frame and serializes it without buffering; it never hard-codes a private Chat HTTP route. When Chat closes at access-token expiry, the BFF uses the existing sealed-session refresh path and reconnects once from the last committed sequence; it does not reset the reducer or silently skip a cursor.

The first local New Chat submit is a two-command adapter sequence, not a hidden Project flow. After validating nonempty content, derive the title as `Array.from(content).slice(0, 80).join("")`: exactly the first 80 Unicode code points, without trimming or a fallback title. Derive a dedicated CreateConversation idempotency key, create the server Conversation with that stable title, atomically replace the guarded local `conv_*` identity with the returned UUID, then Submit with its own distinct stable key. Empty content is rejected before either command. A late create response cannot switch a newer active Conversation; if create succeeds and Submit loses its response, both commands replay by their original keys and digests. The BFF exposes `launch_id` as the mature browser receipt/event `run_id`; Chat maps all events and snapshot run views for that browser run to the same launch ID while Agent keeps its separate internal run identity.

The OpenAPI parity test loads Root-generated operation metadata and asserts every method/path has exactly one BFF route/handler, request and response validation run before/after the backend call, and no undeclared mutation route is present.

**JIT cut requirement 2 — Implement one command envelope**

```ts
type BffCommandContext = Readonly<{
  principalId: string
  siteId: string
  organizationId: string
  operationId: "createConversation" | "submitMessage" | "decideInteraction"
  idempotencyKey: string
}>

type DerivedCommandIdentity = Readonly<{
  commandId: string
  requestDigest: string
}>
```

Derive all identity fields from the sealed IAM session. Only the validated command payload and bounded opaque idempotency key come from the browser. Authenticated `deriveCommandIdentity(context,payload)` returns UUIDv5 over organization + operation + key and SHA-256 over the canonical operation target + validated payload. Pre-auth magic-link request instead uses the resolved Site ID as the UUIDv5 namespace. Reject a browser command UUID/digest and attempts to supply principal, Site, organization or Agent namespace.

**JIT cut requirement 3 — Prove SSE pass-through semantics**

Tests cover response cancellation, reconnect with watermark, `Last-Event-ID`, no bearer leakage, event parsing failure and upstream non-200 propagation.

The `tool.awaiting_approval` browser payload contains Chat's `interaction_id`/generation plus the complete pending target set. Web collects one decision per target and sends the normalized nonempty `decisions[]` in one command; partial target sets stay disabled. No snapshot refresh is required merely to discover the interaction identity.

When Chat returns 409 `SNAPSHOT_REQUIRED`, the engine must stop the old stream, call `ReadConversationSnapshot`, replace owner-derived state at the returned watermark, and reconnect once from that watermark. It must not silently continue from the first retained event or loop on an unchanged cursor.

**JIT cut requirement 4 — Verify and commit**

```bash
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user test -- chat-bff client)
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user lint)
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user typecheck)
git -C /tmp/kokoro-web-slice-a add apps/user/src/app/api/session apps/user/src/lib/server/chat-bff.ts apps/user/src/engine
git -C /tmp/kokoro-web-slice-a commit -m "refactor(web): route conversation commands through Chat"
```

### Milestone 6: Hydrate complete snapshots before applying the event tail

**Files:**
- Modify: `kokoro-web/apps/user/src/core/hydration.ts`, `core/state.ts`, `core/projections.ts`, `engine/machine.ts`, `engine/reattach.ts`
- Test: `kokoro-web/apps/user/src/core/__tests__/hydration.test.ts`, `apps/user/src/engine/__tests__/reattach.test.ts`

**JIT cut requirement 1 — Write the regression RED test**

- Build a snapshot with two messages/parts and one pending HITL but no historical events; assert rendered reducer state contains all three owner facts.
- Set snapshot watermark 41 and feed events 40, 41 and 42; assert only 42 changes state and `lastSeq` becomes 42.
- Hydrate, remove pre-watermark events from the fake server, reconnect in a new machine instance and assert old content plus new tail remains complete.

**JIT cut requirement 2 — Map normalized owner rows into the existing reducer state**

Do not invent a second UI model. Convert snapshot messages/parts/run/interaction into the current `SessionState`, set `lastSeq=watermark`, then feed tail events through the current reducer. Preserve generation guards and event-id deduplication.

**JIT cut requirement 3 — Verify and commit**

```bash
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user test -- hydration reattach)
(cd /tmp/kokoro-web-slice-a && pnpm --filter @kokoro/web-user typecheck)
git -C /tmp/kokoro-web-slice-a add apps/user/src/core apps/user/src/engine
git -C /tmp/kokoro-web-slice-a commit -m "fix(web): hydrate owner snapshot before SSE tail"
```

### Milestone 7: Attach User Web and prove the browser chain

**Files:**
- Create: `scripts/e2e/slice_a_product.py`, `scripts/e2e/test_slice_a_product.py`
- Create in `/tmp/kokoro-web-slice-a`: `tests/e2e/slice-a-chat.spec.ts`, `playwright.config.ts`
- Modify in `/tmp/kokoro-web-slice-a`: root `package.json`, `pnpm-lock.yaml`, `apps/admin/eslint.config.mjs`, `packages/i18n/package.json`
- Create in `/tmp/kokoro-web-slice-a`: `packages/i18n/eslint.config.mjs`
- Modify: `scripts/verify-all.py`

**Interfaces:**
- Consumes: the green Task 2 backend evidence/candidate commits and Tasks 3–6 Web adapters; it creates a fresh database/backend composition rather than relying on those earlier process lifetimes.
- Produces: browser evidence that the thin BFF/hydration layer preserves the already-proven backend semantics.

**JIT cut requirement 1 — Write the browser assertions before orchestration**

First add the exact compatible test runtime from the Web Git root:

```bash
(cd /tmp/kokoro-web-slice-a && pnpm add -Dw --save-exact @playwright/test@1.62.1)
```

Add a Chromium-only config whose `baseURL` comes from `KOKORO_WEB_BASE_URL`. CI installs the matching browser with the lockfile-local `pnpm exec playwright install chromium`; no global Playwright binary is accepted.

Before browser orchestration, close the two known monorepo lint gates instead of hiding them with a User-only filter: replace Admin's legacy `FlatCompat` bridge with the same ESLint 9 flat imports used by the User app, and give `@kokoro/i18n` its own flat config plus exact local `eslint@9.39.1`, `@eslint/js@9.39.1` and `typescript-eslint@8.62.0` dev dependencies. `pnpm -r lint` must exit zero; no ignore blanket or disabled type-aware rule is added.

The test repeats the already-green backend chain through the real browser: server-bound Host → SiteContext selection, magic-link login, sealed auth session, Conversation creation, Submit, snapshot-first render, SSE tail, HITL decision, Agent restart/replay, Chat restart/readback and stale-cursor snapshot recovery. It also asserts browser storage and network responses never contain IAM/Chat/Agent workload credentials or refresh tokens. Owner calls are not mocked.

**JIT cut requirement 2 — Start a fresh native backend plus User Web**

```bash
set -euo pipefail
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-browser-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-browser-fixtures.XXXXXX)"
STATE_PARENT="$(mktemp -d /tmp/kokoro-slice-a-browser-state-parent.XXXXXX)"
STATE_DIR="$STATE_PARENT/state"
export KOKORO_SLICE_A_STATE_DIR="$STATE_DIR"
cleanup_native() {
  if test -e "$STATE_DIR"; then
    uv run --frozen python scripts/slice_a/native.py stop --state-dir "$STATE_DIR" || true
    uv run --frozen python scripts/slice_a/cleanup.py --dir "$STATE_DIR" || true
  fi
  test ! -e "$KOKORO_SLICE_A_SECRET_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  test ! -e "$KOKORO_SLICE_A_FIXTURE_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
  rm -rf -- "$STATE_PARENT"
}
trap cleanup_native EXIT INT TERM
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
uv run --frozen python scripts/slice_a/native.py start --fresh --with-web \
  --state-dir "$KOKORO_SLICE_A_STATE_DIR" \
  --secret-dir "$KOKORO_SLICE_A_SECRET_DIR" \
  --fixture-dir "$KOKORO_SLICE_A_FIXTURE_DIR" \
  --iam /tmp/kokoro-iam-slice-a --model /tmp/kokoro-model-slice-a \
  --capability /tmp/kokoro-capability-slice-a --chat /tmp/kokoro-chat-slice-a \
  --agent /tmp/kokoro-agent-slice-a --web /tmp/kokoro-web-slice-a
# Re-run backend assertions against this fresh database/process lifetime before browser assertions.
KOKORO_SLICE_A_EVIDENCE_PATH=/tmp/kokoro-slice-a-browser-backend.json \
  uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
uv run --frozen pytest scripts/e2e/test_slice_a_product.py -q
(cd /tmp/kokoro-web-slice-a && pnpm exec playwright install chromium)
(cd /tmp/kokoro-web-slice-a && pnpm exec playwright test tests/e2e/slice-a-chat.spec.ts)
cleanup_native
trap - EXIT INT TERM
```

**JIT cut requirement 3 — Commit the Web test; retain Root orchestration for atomic promotion**

```bash
git -C /tmp/kokoro-web-slice-a add tests/e2e/slice-a-chat.spec.ts playwright.config.ts package.json pnpm-lock.yaml apps/admin/eslint.config.mjs packages/i18n
git -C /tmp/kokoro-web-slice-a commit -m "test(web): prove Slice A browser chat"
git diff --check -- scripts/e2e scripts/verify-all.py
```

Root E2E scripts depend on the new gitlinks and release composition, so they remain part of Task 9's single atomic commit.

### Milestone 8: Independently review every candidate repository

**Files:**
- Create: `docs/reports/2026-08-14-slice-a-verification-evidence.md`, `2026-08-14-slice-a-candidates.json`

**JIT cut requirement 1 — Run repository-local full gates**

```bash
# Root
uv run --frozen python scripts/verify-all.py --slice-a --candidate-manifest docs/reports/2026-08-14-slice-a-candidates.json

# IAM/Model/Capability
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
for repo in iam model capability; do
  (cd "/tmp/kokoro-$repo-slice-a" && \
    DATABASE_URL_KOKORO_APP=postgresql://kokoro_app:kokoro@127.0.0.1:1/kokoro pnpm prisma:validate && \
    DATABASE_URL_KOKORO_APP=postgresql://kokoro_app:kokoro@127.0.0.1:1/kokoro pnpm db:generate && \
    pnpm test && pnpm typecheck && pnpm build && pnpm lint)
  (cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18_native.py \
    --label "$repo-review" --cwd "/tmp/kokoro-$repo-slice-a" -- pnpm test:integration)
done

# Chat
(cd /tmp/kokoro-chat-slice-a && \
  npm run check:no-bun && npm test && npm run typecheck && npm run build && npm run lint)
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18_native.py \
  --label chat-review --cwd /tmp/kokoro-chat-slice-a -- npm run test:integration)

# Web
(cd /tmp/kokoro-web-slice-a && \
  pnpm -r test && pnpm -r typecheck && pnpm -r lint && pnpm --filter @kokoro/web-user build)

# Agent
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18_native.py \
  --label agent-review --cwd /tmp/kokoro-agent-slice-a -- uv run pytest -q)
(cd /tmp/kokoro-agent-slice-a && \
  uv run ruff check . && uv run pyright && uv lock --check --no-config)
```

**JIT cut requirement 2 — Run an independent P0/P1/P2 review and re-run changed gates**

Review SQL tenant constraints, owner writer boundaries, RPC exposure, browser identity derivation, crash/replay, zero-call legacy paths and generated provenance. Resolve every P0/P1/P2, commit the fixes in the owning repository and re-run Step 1 for each changed repository before recording any candidate SHA.

**JIT cut requirement 3 — Push reviewed clean HEADs and record exact commits/trees**

The JSON is machine-readable input to `scripts/slice_a/promote.py`; it contains exactly IAM, Model, Capability, Chat, Agent and Web. Each entry records repository URL, the post-review commit and clean-tree digest. It contains no branch name as promotion authority.

```bash
for repo in iam model capability chat agent web; do
  git -C "/tmp/kokoro-$repo-slice-a" status --porcelain --untracked-files=all | grep . && exit 1 || true
  git -C "/tmp/kokoro-$repo-slice-a" push origin HEAD:refs/heads/codex/slice-a
done
```

Only after those pushes succeed, derive every JSON commit/tree value with `git rev-parse HEAD` and `git rev-parse HEAD^{tree}`; do not reuse a pre-review value or copy one from chat output. `promote.py --check-remotes` must resolve the same commit/tree before Step 4.

**JIT cut requirement 4 — Commit only the evidence report**

```bash
git add docs/reports/2026-08-14-slice-a-verification-evidence.md docs/reports/2026-08-14-slice-a-candidates.json
git commit -m "docs: record Slice A verification evidence"
```

### Milestone 9: Atomically promote repositories, pins and release inventory

**Files:**
- Modify: `.gitmodules`, `.github/workflows/contract.yml`, `scripts/INDEX.md`, `scripts/verify-all.py`, `docs/CODEBASE_MAP.md`, `docs/CURRENT.md`, `docs/task.md`
- Add: `scripts/slice_a/**`, `scripts/e2e/**`, `scripts/fixtures/openai_slice_a.py`, `scripts/tests/test_openai_slice_a_fixture.py`, `scripts/tests/test_slice_a_native.py`
- Delete only after replacement: Root `kokoro-session` gitlink
- Add gitlinks: `kokoro-iam`, `kokoro-chat`, `kokoro-model`, `kokoro-capability`
- Preserve gitlinks: `kokoro-platform`, `kokoro-agent`, `kokoro-web`

**JIT cut requirement 1 — Verify all remote candidate commits exist and are immutable**

Never point Root to a local-only commit. Run:

```bash
uv run --frozen python scripts/slice_a/promote.py --manifest docs/reports/2026-08-14-slice-a-candidates.json --check-remotes
```

The command fetches every URL into a temporary bare repository, verifies the exact commit/tree and rejects a dirty local candidate or a branch-only/floating reference.

**JIT cut requirement 2 — Update the Root candidate graph in one commit**

`kokoro-platform` stays pinned as a non-deployed Slice B/C migration source. `kokoro-session` is removed only when `kokoro-chat` at the verified commit is present. The committed native runtime inventory starts only the Slice A capability processes.

```bash
uv run --frozen python scripts/slice_a/promote.py --manifest docs/reports/2026-08-14-slice-a-candidates.json --write
git submodule status
```

`promote.py` is the only step that adds the four new gitlinks, advances Agent/Web, edits `.gitmodules`, deinitializes/removes `kokoro-session` and checks out exact commits. It refuses to touch `kokoro-platform` and rejects any candidate outside the exact six-entry manifest.

**JIT cut requirement 3 — Lock CI and release provenance to the promoted gitlinks**

Extend the source-only `.github/workflows/contract.yml` with checks against the promoted Root gitlinks/exact commits. Its checkout step must fetch the Root history containing the frozen source commit and materialize each promoted output target at the recorded gitlink SHA (private repositories use the dedicated read-only token):

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    submodules: recursive
    token: ${{ secrets.KOKORO_SUBMODULE_TOKEN }}
```

CI reads `sourceRootCommit` from committed Root E2E provenance, proves it is the latest commit that changed `contract/`, installs that commit's own frozen toolchain in a detached worktree, and executes that commit's generator; the candidate Root and promoted gitlinks are output targets only. The workflow uses this exact check shape:

```bash
ROOT_CURRENT="$GITHUB_WORKSPACE"
ROOT_CONTRACT_COMMIT="$(python3 -c 'import json; print(json.load(open("scripts/e2e/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"
CONTRACT_WORKTREE="$RUNNER_TEMP/kokoro-contract-source"
git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"
trap 'git worktree remove --force "$CONTRACT_WORKTREE" 2>/dev/null || true' EXIT
(cd "$CONTRACT_WORKTREE" && pnpm install --frozen-lockfile && uv sync --frozen --group dev)
for consumer_repo in \
  "kokoro-iam:$ROOT_CURRENT/kokoro-iam" \
  "kokoro-chat:$ROOT_CURRENT/kokoro-chat" \
  "kokoro-agent:$ROOT_CURRENT/kokoro-agent" \
  "kokoro-capability:$ROOT_CURRENT/kokoro-capability" \
  "kokoro-model:$ROOT_CURRENT/kokoro-model" \
  "kokoro-web:$ROOT_CURRENT/kokoro-web" \
  "root-e2e:$ROOT_CURRENT"; do
  consumer="${consumer_repo%%:*}"
  repo="${consumer_repo#*:}"
  (cd "$CONTRACT_WORKTREE" && uv run --frozen python contract/generate.py \
    --source-root "$CONTRACT_WORKTREE" --source-commit "$ROOT_CONTRACT_COMMIT" \
    --consumer "$consumer" --repo "$repo" --check)
done
```

Do not hand-edit commit hashes or output digests, and do not run the frozen generator with the later candidate Root's expanded database locks.

**JIT cut requirement 4 — Stage the exact atomic tree and create a detached candidate commit**

```bash
git add .gitmodules .github/workflows/contract.yml scripts/INDEX.md scripts/verify-all.py scripts/slice_a scripts/e2e \
  scripts/fixtures/openai_slice_a.py scripts/tests/test_openai_slice_a_fixture.py scripts/tests/test_slice_a_native.py \
  docs/reports/2026-08-14-slice-a-candidates.json docs/CODEBASE_MAP.md docs/CURRENT.md docs/task.md \
  kokoro-iam kokoro-chat kokoro-model kokoro-capability kokoro-agent kokoro-web kokoro-platform
git add -u -- kokoro-session
test -z "$(git ls-files --stage -- kokoro-session)"
test -n "$(git ls-files --stage -- kokoro-chat)"
git diff --cached --check
TREE="$(git write-tree)"
CANDIDATE="$(printf '%s\n' 'feat: promote SQL-backed Slice A capability graph' | git commit-tree "$TREE" -p HEAD)"
printf '%s\n' "$TREE" >"$(git rev-parse --git-dir)/kokoro-slice-a.tree"
printf '%s\n' "$CANDIDATE" >"$(git rev-parse --git-dir)/kokoro-slice-a.candidate"
rm -rf /tmp/kokoro-slice-a-release
git worktree add --detach /tmp/kokoro-slice-a-release "$CANDIDATE"
git -C /tmp/kokoro-slice-a-release submodule update --init --recursive
(cd /tmp/kokoro-slice-a-release/kokoro-web && pnpm install --frozen-lockfile)
test ! -e /tmp/kokoro-slice-a-release/kokoro-session
test -d /tmp/kokoro-slice-a-release/kokoro-chat
test -f /tmp/kokoro-slice-a-release/scripts/fixtures/openai_slice_a.py
test "$(git -C /tmp/kokoro-slice-a-release rev-parse HEAD:kokoro-platform)" = "$(git rev-parse HEAD:kokoro-platform)"
```

The synthetic commit proves the exact staged tree without moving the branch or committing an unverified state.

**JIT cut requirement 5 — Re-run fresh E2E from the detached candidate**

```bash
set -euo pipefail
cd /tmp/kokoro-slice-a-release
uv sync --frozen
pnpm install --frozen-lockfile
uv run --frozen python scripts/verify-all.py
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-release-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-release-fixtures.XXXXXX)"
STATE_PARENT="$(mktemp -d /tmp/kokoro-slice-a-release-state-parent.XXXXXX)"
STATE_DIR="$STATE_PARENT/state"
export KOKORO_SLICE_A_STATE_DIR="$STATE_DIR"
cleanup_native() {
  if test -e "$STATE_DIR"; then
    uv run --frozen python scripts/slice_a/native.py stop --state-dir "$STATE_DIR" || true
    uv run --frozen python scripts/slice_a/cleanup.py --dir "$STATE_DIR" || true
  fi
  test ! -e "$KOKORO_SLICE_A_SECRET_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  test ! -e "$KOKORO_SLICE_A_FIXTURE_DIR" || uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
  rm -rf -- "$STATE_PARENT"
}
trap cleanup_native EXIT INT TERM
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
uv run --frozen python scripts/slice_a/native.py start --fresh --with-web \
  --state-dir "$KOKORO_SLICE_A_STATE_DIR" \
  --secret-dir "$KOKORO_SLICE_A_SECRET_DIR" \
  --fixture-dir "$KOKORO_SLICE_A_FIXTURE_DIR" \
  --iam kokoro-iam --model kokoro-model --capability kokoro-capability \
  --chat kokoro-chat --agent kokoro-agent --web kokoro-web
uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
uv run --frozen pytest scripts/e2e/test_slice_a_product.py -q
(cd kokoro-web && pnpm exec playwright install chromium && pnpm exec playwright test tests/e2e/slice-a-chat.spec.ts)
git status --porcelain --untracked-files=all | grep . && exit 1 || true
cleanup_native
trap - EXIT INT TERM
cd -
git worktree remove /tmp/kokoro-slice-a-release
```

**JIT cut requirement 6 — Commit the already verified atomic tree**

```bash
EXPECTED_TREE="$(cat "$(git rev-parse --git-dir)/kokoro-slice-a.tree")"
EXPECTED_CANDIDATE="$(cat "$(git rev-parse --git-dir)/kokoro-slice-a.candidate")"
test "$(git write-tree)" = "$EXPECTED_TREE"
test "$(git rev-parse "$EXPECTED_CANDIDATE^{tree}")" = "$EXPECTED_TREE"
test "$(git rev-parse "$EXPECTED_CANDIDATE^")" = "$(git rev-parse HEAD)"
test "$(git log -1 --format=%s "$EXPECTED_CANDIDATE")" = "feat: promote SQL-backed Slice A capability graph"
git commit -m "feat: promote SQL-backed Slice A capability graph"
rm -f "$(git rev-parse --git-dir)/kokoro-slice-a.tree" "$(git rev-parse --git-dir)/kokoro-slice-a.candidate"
```

<!-- slice-a-container-delivery:start -->
### Milestone 10: Deferred container and Compose delivery

This milestone starts only after the native backend/browser closure and atomic Root pin promotion are green.
It is not a prerequisite for the current candidate freeze, backend acceptance or promotion commit.

**Deferred files:**

- Owner-repository `Dockerfile` files.
- Root `docker-compose.infra.yml`, `docker-compose.app.yml`, `docker-compose.ci.yml`.
- Root `config/litellm/slice-a.yaml`, `config/litellm/slice-a-ci.yaml` and deployment documentation.
- Container/Compose validation and image-security tests.

**Deferred acceptance:**

1. Preserve the exact already-promoted commits and native runtime process inventory.
2. Build every final image as non-root, with generated clients/native engines present and no test fixture or
   plaintext secret in layers.
3. Render production, CI and optional Web Compose profiles; reject Platform, Session, MySQL, Mongo and any
   runtime outside the exact Slice A inventory.
4. Apply the Root baseline through a one-shot database initializer, mount the controlled secret/fixture files
   with least privilege and call every real readiness/RPC endpoint.
5. Re-run the same backend, HITL, Agent/Chat restart, retention and browser assertions against the packaged
   graph. Packaging parity is additive evidence and never replaces the native gate.
<!-- slice-a-container-delivery:end -->

## Completion Criteria

- User Web uses IAM and Chat generated clients while preserving sealed auth and reducer/machine behavior.
- Conversation content survives bounded event retention through complete snapshot + watermark-tail hydration.
- Fresh PG18 SiteContext → IAM → Chat → Agent → HITL → restart/replay passes first without Web, then through the browser adapter.
- `kokoro-platform`, Mongo and MySQL are not runtime dependencies for Slice A.
- Root promotion is reproducible from exact remote commits in a detached clean checkout.
- `kokoro-platform` remains available only as the dormant migration source for Slice B/C until those capabilities move.
