---
architectureIndex: 1
rootId: root.scripts.contract
owners:
  - "@LordFoxFairy"
---

# Contract boundary governance

## Responsibilities

Prove that every cross-repository boundary is registered, that each registered operation is backed by a real
contract source, and that each operation is frozen to exactly one transport.

## Non-responsibilities

This gate reads declared contracts only. It does not prove wire behaviour, authorization, deadline enforcement,
receipt durability, or that a provider actually implements a registered operation.

## Public boundary

`check-boundary-registry.mjs` is the supported entrypoint; `check-boundary-registry.test.mjs` defines its
fail-closed behaviour. Policy data is [`contract/registry/boundaries.yaml`](../../contract/registry/boundaries.yaml),
described by [`contract/registry/boundaries.schema.json`](../../contract/registry/boundaries.schema.json).
The registry is JSON-compatible YAML, following `config/architecture/index-roots.yaml`: the filename the spec
mandates, without adding a YAML parser dependency.

`check-boundary-coverage.mjs` is the companion source-to-registry gate. It scans the two internal runtime
consumers (Session and Agent), reduces their detected Platform dependencies to unique service edges, and
requires an `active` registry entry with both the exact provider boundary and the actual consumer.
Repository-pair matching is intentionally insufficient: `service.platform` cannot vouch for `platform.hub`,
and neither can vouch for `platform.litellm`. Web's public BFF plane is outside this narrow scanner and remains
covered by the Admin/OpenAPI and Session browser gates rather than being silently claimed here.

`check_admin_openapi.py` is the supported entrypoint for the Admin browser plane, and
`test_check_admin_openapi.py` defines its fail-closed behaviour. It parses the Fastify route
registrations out of `kokoro-platform/kokoro-platform-admin/src/server.ts` and requires exact set
equality with [`contract/openapi/admin-web-v1.yaml`](../../contract/openapi/admin-web-v1.yaml), so a
route added, removed or re-verbed on either side fails. `--openapi` and `--server` take alternate
paths for fixtures. It is Python because that document is hand-written YAML carrying comments and the
root workspace already provides PyYAML; the sibling registry gate stays on Node because its data is
JSON-compatible.

`check_admin_browser_schemas.py` is the supported entrypoint for the other end of that plane, with
`test_check_admin_browser_schemas.py` defining its fail-closed behaviour. It proves the browser's
hand-written readers in `kokoro-web/apps/admin/lib/schemas.ts` do not contradict the published
contract: every field the browser reads must be declared by the contract schema it is mapped to.
`--openapi` and `--schemas` take alternate paths for fixtures.

It is a gate rather than a generator on purpose. Generating the browser validators from the contract
would *lose* checking for part of this surface: the gateway validates downstream rows only to
`z.array(z.record(z.unknown()))`, so `ResourceRow` is declared with no properties and
`additionalProperties: true` (open decision D4). The hand-written `orderSchema` at least names
`amountMinor` and `currency`, so it currently encodes more field knowledge than the contract does.
The readers also stay deliberately lenient — a dirty row degrades one row instead of blanking the
page. Four readers map onto `ResourceRow` and therefore cannot be verified at all; that count is
printed on every run rather than presented as coverage. When D4 lands, the count drops and generation
becomes the better answer for those four.

## Callers and dependencies

Root CI and contract owners call the checks. They read `contract/proto/`, `contract/spec/`,
`contract/openapi/`, `config/repository/compatibility-matrix.json`, `config/architecture/index-roots.yaml`,
`kokoro-platform/kokoro-platform-admin/src/server.ts` and `kokoro-web/apps/admin/lib/schemas.ts`, and
write nothing.

## Data ownership and events

The registry owns boundary inventory: owner, callers, audience, protocol, deadline, retry class, receipt,
failure owner, and how each operation binds its Site. Wire shapes stay owned by `contract/proto/` and
`contract/spec/`; this directory never becomes a second authority for them.

## Runtime and security

Read-only and deterministic, no new dependencies and no network: the Node gates use the standard library
only, and the Python gates use PyYAML, which the root workspace already provides. Source paths must
stay repository-relative and are rejected if they escape the repository.

## Idempotency, failure, and recovery

Repeated runs on unchanged inputs produce the same single-line result. Any violation exits nonzero with sorted
`snake_case` codes naming the offending boundary, operation and path.

## Extension rules and forbidden dependencies

Register a new boundary in the same change that introduces it, and keep it in step with the compatibility
matrix. Declare `sourceStatus: "machine-readable"` only with a real contract source behind it; a boundary
with no source in this repository must say `declared-only` and be counted, never claim coverage it does not
have. Allowed retry classes are derived from `kokoro.common.v1.RetryClass`; never hardcode that list here.

## Current gotchas

Two blind spots are recorded rather than hidden, and both appear in every successful run.

`model-gateway` is `declared-only`: it is the LiteLLM OpenAI-compatible face and this repository holds no
contract source for it, so its operations get no orphan check at all. It is the one boundary that can drift
without the gate noticing, which is exactly why the count is printed.

Site binding is split three ways and every count is printed. 41 `site`-scoped operations remain
`context-header`: `platform-runtime` sends `x-kokoro-site-id` derived per route, and `session-browser` is
pinned to one Site by the `KOKORO_SITE_ID` process constant rather than by anything on the wire. That number
is Wave T3 debt and must shrink rather than grow. Against it, 8 operations now bind Site as a
`request-field`: three on `platform-admission`, the three effectful credit writes on `platform-runtime`, and
its two model reads (`resolve_model_bindings`, `list_model_labels`), which must agree about a Site's hidden
labels or the catalogue offers models resolution then refuses.
The gate proves each claim against that operation's own request shape rather than trusting the declaration.

`context-header` is the weaker of the two claims and is not proven at all: the gate cannot see whether a
provider reads the header it is declared to read. `list_model_labels` was declared `context-header` while its
handler ignored the header entirely and applied no Site filter — the caller sent it, so the declaration
looked satisfied from the wire. Treat the count as unverified debt, not as coverage.

`platform-admission` is the first `contract-only` boundary: its shape is published in
`contract/proto/kokoro/platform/admission/v1/admission.proto`, but no provider implements it, so it is
deliberately absent from the compatibility matrix. The matrix drives the runtime gate, and listing an
unimplemented protocol there would assert a capability that does not exist. Registering it as `active`
before a provider ships fails.

The `request-field` proof is per request message for proto sources. For spec YAML it depends on how the
source declares operations: when their ids derive from object names the proof is per operation, resolved
against that operation's own request object. Only a block-mapping section such as `endpoints`, which
declares no fields of its own, still falls back to a file-wide match — weaker evidence, so those operations
are tracked separately rather than presented as per-operation proof. The file-wide form previously applied
everywhere, which let one object's `siteId` vouch for siblings that had none. Every `deadlineMs` is
`null` because no boundary declares a deadline in code yet; that is a recorded fact, not an implied default.

The Admin gate scopes itself to the browser plane and names its exclusions rather than skipping them
quietly: `/` serves HTML, `/healthz` and `/metrics` are probe endpoints registered by platform-kit
helpers, and `kokoro.platform.admin.v1.AdminAuthService` is the privileged Connect plane the transport
spec keeps separate. Declaring an excluded path in the document fails, and an unrecognised
`register*Route` helper fails too, because such a helper registers routes this gate cannot see.

## Verification

Run `node --test scripts/contract/*.test.mjs` followed by `node scripts/contract/check-boundary-registry.mjs`
and `node scripts/contract/check-boundary-coverage.mjs`,
then `uv run --locked python -m pytest scripts/contract/test_check_admin_openapi.py
scripts/contract/test_check_admin_browser_schemas.py -q`,
`uv run --locked python scripts/contract/check_admin_openapi.py` and
`uv run --locked python scripts/contract/check_admin_browser_schemas.py`.

The Node checks need no install; the Python ones need `uv sync --locked` first. Both were replayed
from a bare recursive clone at the pinned state. Read exit codes directly rather than through a pipe,
which reports the last command's status instead of the gate's.
