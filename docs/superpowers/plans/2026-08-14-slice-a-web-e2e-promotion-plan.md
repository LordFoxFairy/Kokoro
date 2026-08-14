# Slice A Backend E2E, Web Adapter and Atomic Promotion Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before a lane starts, its next milestone MUST be expanded into a separately reviewed JIT implementation cut with exact files, actual RED test/code, self-contained commands and one precise commit; workers never invent omitted code from this roadmap.

**Goal:** Prove the complete SQL-backed Site → IAM → Chat → Agent → HITL → restart/replay backend chain without a browser, then connect the mature User Web through thin generated adapters and atomically promote the reviewed repositories.

**Architecture:** Root first composes PostgreSQL, Redis, LiteLLM, Site, IAM, Model, Capability, Chat and Agent and drives them through generated service clients; User Web is absent from this backend acceptance gate. After that gate passes, browser traffic remains same-origin HTTP/SSE through the User BFF, which uses generated owner clients and preserves the existing reducer/machine. Root owns repeatable PG18 E2E, exact candidate pins and the final release inventory. `kokoro-platform` remains pinned but dormant as the Slice B/C migration source; `kokoro-session` is replaced by `kokoro-chat` only after both backend and browser gates pass.

**Tech Stack:** PostgreSQL 18, Redis, LiteLLM, Docker Compose, Python 3.11 gRPC/HTTP E2E clients, Next.js User app, TypeScript, generated Connect clients, Zod, Vitest and Playwright.

## Global Constraints

- Root composition/E2E changes stay in the Root worktree until the final atomic commit. Web changes work only in `/tmp/kokoro-web-slice-a`, created from `kokoro-web@f3936befb7ae4c219273ae9b7f4efb97cb6a1425`, and the exact frozen Root contract commit. Do not edit the canonical Web submodule checkout.
- Preserve existing Web reducer, machine, SSE reconnect, idempotency, HITL, sealed session envelope and mobile UI. Change adapters, not state semantics.
- Browser never receives IAM, Chat or Agent service credentials and never calls service RPC directly.
- Web's server-only clients use the mounted Web workload token to call Site 7201, IAM 7202 and Chat 7205; the BFF also forwards only the IAM access JWT recovered from its sealed httpOnly envelope.
- Snapshot hydration must include complete messages/parts, active run, active interaction and watermark; bounded stream retention must not erase conversation history.
- No `kokoro-platform` API, Hub, Mongo, MySQL, Storage, Entitlement or Payment process participates in Slice A E2E.
- The backend service E2E must pass before any Web adapter task begins. Root pin/release changes are one final commit after all candidate repositories are clean, reviewed and reproducible from exact commits.

---

### Milestone 1: Add the Root backend-only Slice A integration composition

**Files:**
- Modify: `docker-compose.infra.yml`, `docker-compose.app.yml`
- Create: `docker-compose.ci.yml`
- Create: `config/litellm/slice-a.yaml`, `config/litellm/slice-a-ci.yaml`
- Create: `scripts/slice_a/up.py`, `wait_ready.py`, `seed.py`, `create_secrets.py`, `create_fixture_dir.py`, `cleanup.py`, `promote.py`, `validate_compose.py`, `__init__.py`
- Create: `scripts/fixtures/openai_slice_a.py`, `scripts/tests/test_openai_slice_a_fixture.py`
- Create: `scripts/tests/test_slice_a_compose.py`
- Modify: `deploy/.env.example`, `scripts/INDEX.md`, `deploy/README.md`

**Interfaces:**
- Consumes: clean Site, IAM, Model, Capability, Chat and Agent candidate commits plus committed Root baseline/contracts.
- Produces: a browser-independent backend profile and an optional `web` profile used only after Task 2 passes.

**JIT cut requirement 1 — Write a failing composition inventory test**

Parse the fully rendered Compose model and assert the unprofiled backend service set plus explicit optional profiles:

```python
BACKEND_SERVICES = {
    "postgres", "redis", "database-init", "litellm",
    "site", "iam", "model", "capability", "chat", "agent",
}
CI_PROFILE_SERVICES = {"model-fixture"}
WEB_PROFILE_SERVICES = {"user-web"}
```

Assert `model-fixture` has `profiles: ["ci"]`, `user-web` has `profiles: ["web"]`, unprofiled production shape is `BACKEND_SERVICES`, CI is `BACKEND_SERVICES | CI_PROFILE_SERVICES`, and browser CI is all three sets. Assert no active service image, environment or dependency contains Platform, Session, MySQL or Mongo. `database-init` is the only service that reads `database/baseline/kokoro.sql`, exits successfully before applications start, and is never a long-running process. The promotion fixture rejects branch names, missing remote commit objects and tree-digest mismatches.

The same RED test creates a temporary secret directory and asserts `create_secrets.py` writes the exact controlled manifest: `web.workload-token`, `chat.workload-token`, `agent.workload-token`, `iam.refresh-derivation-key`, `web.session-key`, `litellm.api-key` as independent random 32-byte/64-lowercase-hex files mode `0600`; plus `iam.jwt-private.pem` mode `0600` and its matching `iam.jwt-public.pem` mode `0644`. Re-running with a symlink, wrong mode, mismatched keypair or unexpected ninth file fails closed. `cleanup.py` removes only the explicitly supplied generated directory and refuses `/`, an empty path or a directory without its generated marker.

User Web receives `web.session-key` only through `KOKORO_WEB_SESSION_KEY_FILE`; its adapter reads the file once, uses the bytes for the existing session envelope and derives the magic-state HKDF subkey. Slice A production config removes the direct `KOKORO_WEB_SESSION_SECRET` value path so there is one name and one mounted authority.

`create_fixture_dir.py` creates a separately marked mode-0700 directory with one empty `magic-links/` child. Compose bind-mounts only that child into IAM in `KOKORO_RUNTIME_MODE=fixture`; no other service may write it. Tests reject enabling the fixture mailer outside the `ci` profile and accept only an already-created, empty, caller-owned, mode-0700 non-symlink directory; it atomically adds its marker and `magic-links/`, and rejects non-empty/already-marked/symlink/wrong-owner/wrong-mode paths.

**JIT cut requirement 2 — Define the minimal backend composition**

- PostgreSQL 18, Redis and the existing LiteLLM-compatible gateway are the only production-shaped Slice A infrastructure. Repeatable CI also starts the Root-owned `model-fixture` test service; it is never emitted in the production release profile. The gateway mounts Root-owned `config/litellm/slice-a.yaml`; it never mounts a dormant Platform file.
- Site, IAM, Model, Capability, Chat and Agent are independent processes. User Web is optional profile `web` and is not started by the backend gate.
- Root applies `database/baseline/kokoro.sql` before any application starts.
- Before Compose, `create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"` creates the controlled manifest. Compose declares files as read-only secrets and mounts only the minimum set: Web gets web workload + session key; Site gets web workload; IAM gets web/chat workload + refresh/JWT keys; Chat gets web/chat workload; Agent gets chat/agent workload + LiteLLM key; Model/Capability get agent workload; LiteLLM gets its key. No secret value is placed in environment values or image layers.
- Agent calls real LiteLLM on 4000 using its mounted gateway key. Base `slice-a.yaml` is the release configuration and requires an operator-supplied upstream model/base URL/provider credential file; startup fails if they are absent, so the unprofiled release never silently points at a fixture. `docker-compose.ci.yml` replaces it with `slice-a-ci.yaml`, which maps only model `slice-a-fixture` to OpenAI-compatible `http://model-fixture:4010/v1`. `model-fixture` remains `profiles: ["ci"]` and is absent from rendered production release config.
- `docker-compose.ci.yml` overrides the same IAM service with `KOKORO_RUNTIME_MODE=fixture` and a read/write bind of only the generated `magic-links/` directory; the base/unprofiled IAM service has no fixture env or mount. Its `FixtureFileMagicLinkMailer`: it writes `${request_id}.json.tmp`, fsyncs, atomically renames to `${request_id}.json` mode `0600`, and the bounded JSON is exactly `{requestId,normalizedEmail,token,expiresAt}`. Root E2E polls the caller-known request ID, validates email/expiry, reads the token once and deletes the file. Production startup rejects this adapter and requires the real mailer.
- Health/readiness proves each process's DB/RPC dependencies without impersonating a user.
- Every candidate build context is parameterized, for example `${KOKORO_SITE_CONTEXT:-./kokoro-site}`. Before promotion E2E supplies `/tmp/kokoro-*-slice-a`; after promotion defaults resolve to Root gitlinks.

`openai_slice_a.py` is a test-only OpenAI Chat Completions server. For the first request containing user text `slice-a-hitl`, its streaming response contains exactly one `request_human` tool call with stable ID `call_slice_a_approval`, JSON arguments `{"kind":"approval","prompt":"Approve Slice A?"}`, `finish_reason="tool_calls"` and usage `{prompt_tokens:11, completion_tokens:7, total_tokens:18}`. When the request history contains that tool result, it streams `Slice A approved.` with usage `{prompt_tokens:19, completion_tokens:4, total_tokens:23}`. Any other model/prompt returns 400. The fixture test sends both requests directly, then through real LiteLLM, and asserts identical tool-call/content/usage facts reach the Agent-compatible OpenAI client.

**JIT cut requirement 3 — Verify the backend profile without committing the atomic cut**

```bash
uv run --frozen pytest scripts/tests/test_slice_a_compose.py scripts/tests/test_openai_slice_a_fixture.py -q
export KOKORO_SITE_CONTEXT=/tmp/kokoro-site-slice-a
export KOKORO_IAM_CONTEXT=/tmp/kokoro-iam-slice-a
export KOKORO_MODEL_CONTEXT=/tmp/kokoro-model-slice-a
export KOKORO_CAPABILITY_CONTEXT=/tmp/kokoro-capability-slice-a
export KOKORO_CHAT_CONTEXT=/tmp/kokoro-chat-slice-a
export KOKORO_AGENT_CONTEXT=/tmp/kokoro-agent-slice-a
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-fixtures.XXXXXX)"
trap 'uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR"; uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"' EXIT
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml config >/tmp/kokoro-slice-a-production-compose.yaml
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci config >/tmp/kokoro-slice-a-ci-compose.yaml
uv run --frozen python scripts/slice_a/validate_compose.py --production /tmp/kokoro-slice-a-production-compose.yaml --ci /tmp/kokoro-slice-a-ci-compose.yaml
git diff --check -- docker-compose.infra.yml docker-compose.app.yml docker-compose.ci.yml config/litellm deploy scripts/slice_a scripts/fixtures scripts/tests
```

These Root files are part of the final pin/runtime atomic cut and remain uncommitted until Task 9. Do not create an intermediate commit whose default build contexts do not yet exist.

### Milestone 2: Prove the real backend chain and restart invariants

**Files:**
- Create: `scripts/e2e/generated/**` from the frozen Root contracts
- Create: `scripts/e2e/slice_a_backend.py`, `scripts/e2e/test_slice_a_backend.py`
- Modify: `scripts/verify-all.py`

**Interfaces:**
- Consumes: the Task 1 backend profile and exact generated Site/IAM/Chat clients; downstream Agent/Capability/Model behavior is observed only through Chat product APIs.
- Produces: the first release-blocking Slice A milestone, independent of Browser and Web code.

**JIT cut requirement 1 — Write RED backend assertions before orchestration**

The pytest fixture must call real product service endpoints and fail if any owner is replaced by an in-process fake. It authenticates as the Web workload only and reaches downstream Agent/Capability/Model exclusively through Chat; it never loads Chat/Agent workload secrets or calls their private RPCs directly. Wrong-token private-boundary checks live in each owner repository and the Compose security suite. It performs exactly:

1. Apply the committed Root baseline to a fresh PostgreSQL 18 database, then invoke the Site and Model images' owner-only versioned bootstrap commands. Assert exact replay succeeds, drift fails, and Root E2E performs no direct business-table INSERT.
2. Call `SiteService.ResolveSiteByHost`.
3. Call IAM `RequestMagicLink`, read the local fixture mailer's token, then `ConsumeMagicLink`; assert Principal, personal Organization, owner Membership, role bindings and all five Slice A permissions.
4. Call Chat `CreateConversation`, then authorize and `SubmitMessage` with caller-generated command IDs.
5. Observe Agent claim, empty Capability snapshot resolution, Model selection and the existing deterministic LiteLLM/GA execution path.
6. Read Chat snapshot and SSE tail; assert user/assistant messages, run view and a deterministic HITL request.
7. Call Chat `DecideInteraction`; assert Agent control receipt, resume and exactly one terminal projection.
8. Stop Agent after a durable event commit, restart it, and assert outbox replay creates no duplicate event/effect. Stop and restart Chat and assert the same complete snapshot.
9. Run the production retention cycle, request an expired cursor and assert typed `SNAPSHOT_REQUIRED`; refetch snapshot at its watermark and observe the new tail without history loss.
10. Replay each mutating command with the same digest, then with a changed digest; assert stable result followed by conflict.

**JIT cut requirement 2 — Verify the committed Root-owned test clients and provenance**

```bash
ROOT_CONTRACT_COMMIT="$(uv run --frozen python -c 'import json; print(json.load(open("scripts/e2e/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"
uv run --frozen python contract/generate.py --source-root "$(git rev-parse --show-toplevel)" --source-commit "$ROOT_CONTRACT_COMMIT" --consumer root-e2e --repo . --check
```

The generated Python clients were committed by the Root contract plan as a descendant output commit and are test harness code only; services still use their own generated consumers. The provenance file must pin the same Root contract commit and source digest used by every child.

**JIT cut requirement 3 — Run twice from fresh state with no Web process**

```bash
export KOKORO_SITE_CONTEXT=/tmp/kokoro-site-slice-a
export KOKORO_IAM_CONTEXT=/tmp/kokoro-iam-slice-a
export KOKORO_MODEL_CONTEXT=/tmp/kokoro-model-slice-a
export KOKORO_CAPABILITY_CONTEXT=/tmp/kokoro-capability-slice-a
export KOKORO_CHAT_CONTEXT=/tmp/kokoro-chat-slice-a
export KOKORO_AGENT_CONTEXT=/tmp/kokoro-agent-slice-a
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-fixtures.XXXXXX)"
cleanup_slice_a() {
  docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci down -v --remove-orphans || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
}
trap cleanup_slice_a EXIT
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"

docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci down -v --remove-orphans
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci up -d --build
KOKORO_SLICE_A_EVIDENCE_PATH=/tmp/kokoro-slice-a-first.json \
  uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q

docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci down -v --remove-orphans
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci up -d --build
KOKORO_SLICE_A_EVIDENCE_PATH=/tmp/kokoro-slice-a-second.json \
  uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
uv run --frozen python scripts/e2e/slice_a_backend.py compare-evidence \
  /tmp/kokoro-slice-a-first.json /tmp/kokoro-slice-a-second.json
cleanup_slice_a
trap - EXIT
```

Each `down -v` removes the PostgreSQL volume; on each `up`, `database-init` applies the committed baseline to a newly created database before owners start. Assert no `user-web` container exists. The two fresh runs must produce the same baseline digest, PostgreSQL catalog inventory and seed result: exactly 50 owner tables plus four checkpointer tables and no unexpected business uniqueness.

**JIT cut requirement 4 — Freeze the backend milestone**

```bash
uv run --frozen python scripts/verify-all.py --slice-a-backend
git diff --check -- scripts/e2e scripts/verify-all.py
```

Any backend RED stops execution here. Do not begin Task 3 and do not use a Web mock to bypass it. Root E2E files remain uncommitted until Task 9 because they depend on candidate gitlinks/build contexts.

### Milestone 3: Generate IAM and Chat clients for the User BFF

**Files:**
- Create: `kokoro-web/apps/user/src/generated/site/**`, `iam/**`, `chat/**`, `http/**`
- Create: `kokoro-web/apps/user/src/lib/server/site-client.ts`, `iam-client.ts`, `chat-client.ts`, `service-identity.ts`
- Modify in `/tmp/kokoro-web-slice-a`: `apps/user/package.json`, `pnpm-lock.yaml`, `apps/user/src/lib/server/INDEX.md`
- Test: `kokoro-web/apps/user/src/lib/server/__tests__/service-clients.test.ts`

**JIT cut requirement 1 — Verify the Root-generated consumer closure, then write the failing server-client test**

```bash
ROOT_CONTRACT_COMMIT="$(uv run --frozen python -c 'import json; print(json.load(open("scripts/e2e/generated/provenance.json"))["sourceRootCommit"])')"
test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"
uv run --frozen python contract/generate.py --source-root "$(git rev-parse --show-toplevel)" --source-commit "$ROOT_CONTRACT_COMMIT" --consumer kokoro-web --repo /tmp/kokoro-web-slice-a --check
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
  site: SiteServiceClient
  iam: IamAuthenticationServiceClient
  chatCommands: ChatCommandServiceClient
  chatQueries: ChatQueryServiceClient
}

export function createUserBackendClients(env: NodeJS.ProcessEnv): UserBackendClients
```

Read service endpoints and credentials only from server environment. Reject browser bundles that import the factory through an architecture test.

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
- Consumes Site/IAM generated clients.
- Produces the existing sealed browser auth session containing only IAM identity/session context; it does not create a Project or Conversation during login.

**JIT cut requirement 1 — Write RED tests**

- Mock IAM login returning access/refresh tokens; assert the BFF response and browser storage omit both while the httpOnly sealed cookie decrypts to them server-side.
- Rotate once, replay the old refresh token and assert the envelope is cleared plus IAM's family-replay error is preserved.
- Complete login and assert the envelope contains principal/Site/organization/auth-session context, while Chat receives zero calls.
- Send forged principal/Site/organization headers and assert the BFF forwards only values recovered from the envelope.

**JIT cut requirement 2 — Replace only the backend adapter**

Keep the current httpOnly AES-GCM envelope and Origin/CSRF fences. Replace `AuthConfig` legacy `userBaseUrl/sessionBaseUrl/siteId/hubBaseUrl/paymentBaseUrl` with exact Site/IAM/Chat endpoints plus workload credential. `site.ts` resolves Host through the generated Site Connect client before `RequestMagicLink`; there is no parallel Site HTTP client.

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

The test repeats the already-green backend chain through the real browser: Host-based Site resolve, magic-link login, sealed auth session, Conversation creation, Submit, snapshot-first render, SSE tail, HITL decision, Agent restart/replay, Chat restart/readback and stale-cursor snapshot recovery. It also asserts browser storage and network responses never contain IAM/Chat/Agent workload credentials or refresh tokens. Owner calls are not mocked.

**JIT cut requirement 2 — Start a fresh backend plus the optional Web profile**

```bash
export KOKORO_SITE_CONTEXT=/tmp/kokoro-site-slice-a
export KOKORO_IAM_CONTEXT=/tmp/kokoro-iam-slice-a
export KOKORO_MODEL_CONTEXT=/tmp/kokoro-model-slice-a
export KOKORO_CAPABILITY_CONTEXT=/tmp/kokoro-capability-slice-a
export KOKORO_CHAT_CONTEXT=/tmp/kokoro-chat-slice-a
export KOKORO_AGENT_CONTEXT=/tmp/kokoro-agent-slice-a
export KOKORO_WEB_CONTEXT=/tmp/kokoro-web-slice-a
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-browser-fixtures.XXXXXX)"
cleanup_slice_a_browser() {
  docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci --profile web down -v --remove-orphans || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
}
trap cleanup_slice_a_browser EXIT
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci --profile web up -d --build
# Re-run the backend product assertions against this fresh database before the browser assertion.
KOKORO_SLICE_A_EVIDENCE_PATH=/tmp/kokoro-slice-a-browser-backend.json \
  uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
uv run --frozen pytest scripts/e2e/test_slice_a_product.py -q
(cd /tmp/kokoro-web-slice-a && pnpm exec playwright install chromium)
(cd /tmp/kokoro-web-slice-a && pnpm exec playwright test tests/e2e/slice-a-chat.spec.ts)
cleanup_slice_a_browser
trap - EXIT
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

# Site/IAM/Model/Capability
ROOT_SOURCE=/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
for repo in site iam model capability; do
  (cd "/tmp/kokoro-$repo-slice-a" && \
    DATABASE_URL_KOKORO_APP=postgresql://kokoro_app:kokoro@127.0.0.1:1/kokoro pnpm prisma:validate && \
    DATABASE_URL_KOKORO_APP=postgresql://kokoro_app:kokoro@127.0.0.1:1/kokoro pnpm db:generate && \
    pnpm test && pnpm typecheck && pnpm build && pnpm lint && docker build -t "kokoro-$repo:slice-a" .)
  (cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
    --label "$repo-review" --cwd "/tmp/kokoro-$repo-slice-a" -- pnpm test:integration)
done

# Chat
(cd /tmp/kokoro-chat-slice-a && \
  npm run check:no-bun && npm test && npm run typecheck && npm run build && npm run lint && \
  docker build -t kokoro-chat:slice-a .)
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label chat-review --cwd /tmp/kokoro-chat-slice-a -- npm run test:integration)

# Web
(cd /tmp/kokoro-web-slice-a && \
  pnpm -r test && pnpm -r typecheck && pnpm -r lint && pnpm --filter @kokoro/web-user build)

# Agent
(cd "$ROOT_SOURCE" && uv run --frozen python scripts/database/run_in_fresh_pg18.py \
  --label agent-review --cwd /tmp/kokoro-agent-slice-a -- uv run pytest -q)
(cd /tmp/kokoro-agent-slice-a && \
  uv run ruff check . && uv run pyright && uv lock --check --no-config)
```

**JIT cut requirement 2 — Run an independent P0/P1/P2 review and re-run changed gates**

Review SQL tenant constraints, owner writer boundaries, RPC exposure, browser identity derivation, crash/replay, zero-call legacy paths and generated provenance. Resolve every P0/P1/P2, commit the fixes in the owning repository and re-run Step 1 for each changed repository before recording any candidate SHA.

**JIT cut requirement 3 — Push reviewed clean HEADs and record exact commits/trees**

The JSON is machine-readable input to `scripts/slice_a/promote.py`; it contains exactly Site, IAM, Model, Capability, Chat, Agent and Web. Each entry records repository URL, the post-review commit and clean-tree digest. It contains no branch name as promotion authority.

```bash
for repo in site iam model capability chat agent web; do
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
- Modify: `.gitmodules`, `.github/workflows/contract.yml`, `docker-compose.infra.yml`, `docker-compose.app.yml`
- Add: `docker-compose.ci.yml`, `config/litellm/slice-a.yaml`, `config/litellm/slice-a-ci.yaml`
- Modify: `deploy/.env.example`, `deploy/README.md`, `scripts/INDEX.md`, `scripts/verify-all.py`, `docs/CODEBASE_MAP.md`, `docs/CURRENT.md`, `docs/task.md`
- Add: `scripts/slice_a/**`, `scripts/e2e/**`, `scripts/fixtures/openai_slice_a.py`, `scripts/tests/test_openai_slice_a_fixture.py`, `scripts/tests/test_slice_a_compose.py`
- Delete only after replacement: Root `kokoro-session` gitlink
- Add gitlinks: `kokoro-site`, `kokoro-iam`, `kokoro-chat`, `kokoro-model`, `kokoro-capability`
- Preserve gitlinks: `kokoro-platform`, `kokoro-agent`, `kokoro-web`

**JIT cut requirement 1 — Verify all remote candidate commits exist and are immutable**

Never point Root to a local-only commit. Run:

```bash
uv run --frozen python scripts/slice_a/promote.py --manifest docs/reports/2026-08-14-slice-a-candidates.json --check-remotes
```

The command fetches every URL into a temporary bare repository, verifies the exact commit/tree and rejects a dirty local candidate or a branch-only/floating reference.

**JIT cut requirement 2 — Update the Root candidate graph in one commit**

`kokoro-platform` stays pinned as a non-deployed Slice B/C migration source. `kokoro-session` is removed only when `kokoro-chat` at the verified commit is present. The release inventory starts only the Slice A capability processes.

```bash
uv run --frozen python scripts/slice_a/promote.py --manifest docs/reports/2026-08-14-slice-a-candidates.json --write
git submodule status
```

`promote.py` is the only step that adds the five new gitlinks, advances Agent/Web, edits `.gitmodules`, deinitializes/removes `kokoro-session` and checks out exact commits. It refuses to touch `kokoro-platform`.

**JIT cut requirement 3 — Lock CI and release provenance to the promoted gitlinks**

Replace the floating sibling-`main` checkouts in `.github/workflows/contract.yml` with the Root gitlinks/exact commits. Run consumer checks from the clean candidate Root commit whose registered contract sources are byte-identical to the frozen source commit. Do not hand-edit commit hashes or output digests.

**JIT cut requirement 4 — Stage the exact atomic tree and create a detached candidate commit**

```bash
git add .gitmodules .github/workflows/contract.yml docker-compose.infra.yml docker-compose.app.yml docker-compose.ci.yml \
  config/litellm/slice-a.yaml config/litellm/slice-a-ci.yaml deploy/.env.example deploy/README.md scripts/INDEX.md scripts/verify-all.py scripts/slice_a scripts/e2e \
  scripts/fixtures/openai_slice_a.py scripts/tests/test_openai_slice_a_fixture.py scripts/tests/test_slice_a_compose.py \
  docs/reports/2026-08-14-slice-a-candidates.json docs/CODEBASE_MAP.md docs/CURRENT.md docs/task.md \
  kokoro-site kokoro-iam kokoro-chat kokoro-model kokoro-capability kokoro-agent kokoro-web kokoro-platform
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
cd /tmp/kokoro-slice-a-release
uv sync --frozen
pnpm install --frozen-lockfile
uv run --frozen python scripts/verify-all.py
export KOKORO_SLICE_A_SECRET_DIR="$(mktemp -d /tmp/kokoro-slice-a-release-secrets.XXXXXX)"
export KOKORO_SLICE_A_FIXTURE_DIR="$(mktemp -d /tmp/kokoro-slice-a-release-fixtures.XXXXXX)"
cleanup_release() {
  docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci --profile web down -v --remove-orphans || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_SECRET_DIR" || true
  uv run --frozen python scripts/slice_a/cleanup.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR" || true
}
trap cleanup_release EXIT
uv run --frozen python scripts/slice_a/create_secrets.py --dir "$KOKORO_SLICE_A_SECRET_DIR"
uv run --frozen python scripts/slice_a/create_fixture_dir.py --dir "$KOKORO_SLICE_A_FIXTURE_DIR"
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci up -d --build
uv run --frozen pytest scripts/e2e/test_slice_a_backend.py -q
docker compose -f docker-compose.infra.yml -f docker-compose.app.yml -f docker-compose.ci.yml --profile ci --profile web up -d --build
uv run --frozen pytest scripts/e2e/test_slice_a_product.py -q
(cd kokoro-web && pnpm exec playwright install chromium && pnpm exec playwright test tests/e2e/slice-a-chat.spec.ts)
git status --porcelain --untracked-files=all | grep . && exit 1 || true
cleanup_release
trap - EXIT
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

## Completion Criteria

- User Web uses IAM and Chat generated clients while preserving sealed auth and reducer/machine behavior.
- Conversation content survives bounded event retention through complete snapshot + watermark-tail hydration.
- Fresh PG18 Site → IAM → Chat → Agent → HITL → restart/replay passes first without Web, then through the browser adapter.
- `kokoro-platform`, Mongo and MySQL are not runtime dependencies for Slice A.
- Root promotion is reproducible from exact remote commits in a detached clean checkout.
- `kokoro-platform` remains available only as the dormant migration source for Slice B/C until those capabilities move.
