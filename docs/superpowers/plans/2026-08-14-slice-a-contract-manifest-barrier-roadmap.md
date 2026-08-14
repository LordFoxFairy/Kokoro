# Slice A Contract Manifest Barrier Phase Roadmap

> **Document type:** Reviewed phase roadmap, not direct `executing-plans` input. Before each milestone starts, create and independently review a small JIT implementation cut containing complete source/test code, self-contained RED→GREEN commands and one exact commit boundary.

**Goal:** Starting from the already-reviewed authority-validation commit, produce the second clean Root contract-source commit containing exact Protobuf/OpenAPI sources, the first Buf breaking image and deterministic consumer-scoped generation; then generate Root E2E outputs in a separate descendant-output commit.

**Architecture:** The reviewed YAML is the only design input. A small Root renderer produces `.proto` and OpenAPI source from it, then Buf/Redocly and independent descriptor tests prove the rendered artifacts. Generation reads a committed Root tree, emits only the manifest-declared consumer file closure and records output hashes. This cut freezes shared protocol before the independent backend lanes start; it does not create SQL tables or business services.

**Tech Stack:** Python 3.11, uv, PyYAML 6.0.3, grpcio-tools 1.83.0, protobuf 6.33.6, Node.js 22+, pnpm, Buf 1.72.0, Protobuf-ES 2.14.0, Redocly CLI 2.46.1, pytest.

**Reviewed inputs:**
- `docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml`
- `docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.md`
- `docs/superpowers/plans/2026-08-14-sql-backed-chat-slice-a-master-plan.md`
- committed `contract/slice-a-contract-manifest.yaml`, `contract/validate_slice_a_manifest.py` and its authority mutation tests from `feat(contract): install Slice A machine authority`

**Commit boundaries:** first, one Root-only contract-source commit named `feat(contract): freeze Slice A service contracts`; second, a descendant-output commit named `chore(contract): generate Slice A Root E2E client`. Neither contains SQL, child gitlinks, deployment files or BOM changes. The source provenance SHA is always the first commit, never the output commit.

---

### Milestone 1: Lock the Root contract toolchain

**Files:**
- Create: `package.json`
- Create: `pnpm-lock.yaml`
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `.node-version`
- Test: `contract/tests/test_contract_toolchain.py`

**Step 1: Write the toolchain RED test**

Create `contract/tests/test_contract_toolchain.py` with these exact assertions:

```python
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_contract_toolchain_is_exactly_pinned() -> None:
    package = json.loads((ROOT / "package.json").read_text())
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["engines"] == {"node": ">=22 <25"}
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protoc-gen-es": "2.14.0",
        "@redocly/cli": "2.46.1",
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == ">=3.11,<3.14"
    assert project["project"]["dependencies"] == [
        "grpcio-tools==1.83.0",
        "protobuf==6.33.6",
        "PyYAML==6.0.3",
    ]
```

Run:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
python3 -m pytest contract/tests/test_contract_toolchain.py -q
```

Expected: RED because the four toolchain files do not exist.

**Step 2: Add exact manifests and locks**

`package.json` must contain only private Root tooling, the exact versions above and scripts `contract:format`, `contract:lint`, `contract:render`, `contract:check`. `pyproject.toml` must declare only the three runtime dependencies above plus pytest `8.4.2` in dependency group `dev`; no floating range is allowed.

Run the deterministic bootstrap:

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
corepack enable
pnpm install --lockfile-only
pnpm install --frozen-lockfile
uv lock
uv sync --frozen --group dev
pnpm exec buf --version | grep -Fx '1.72.0'
pnpm exec protoc-gen-es --version | grep -F '2.14.0'
pnpm exec redocly --version | grep -F '2.46.1'
uv run python -c 'import grpc_tools, google.protobuf, yaml; print("python-contract-tools-ok")'
uv run pytest contract/tests/test_contract_toolchain.py -q
```

Expected: GREEN and no registry lookup is needed by later `--frozen` commands.

**Step 3: Keep toolchain preparation in the second source commit**

Do not commit yet. This task is preparation inside the contract-source commit, on top of the already committed authority cut. Confirm:

```bash
git diff --check -- package.json pnpm-lock.yaml pyproject.toml uv.lock .node-version contract/tests/test_contract_toolchain.py
```

---

### Milestone 2: Reuse and extend validation of the installed machine authority

**Files:**
- Reuse unchanged: `contract/slice-a-contract-manifest.yaml`, `contract/validate_slice_a_manifest.py`, `contract/tests/test_slice_a_manifest_authority.py`
- Create: `contract/tests/test_slice_a_renderer_contract.py`

**Step 1: Prove the prerequisite authority commit is present and unchanged**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
cmp docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
```

**Step 2: Write the renderer-facing structural test**

The new test imports the committed validator instead of creating a second one, then asserts all renderer-specific facts without snapshots or substring matching:

```python
assert manifest["authority"] == "machine"
assert len(manifest["protobuf"]["files"]) == 9
assert len(manifest["protobuf"]["services"]) == 8
assert sum(len(s["methods"]) for s in manifest["protobuf"]["services"]) == 19
stream = next(m for s in manifest["protobuf"]["services"] for m in s["methods"] if m["name"] == "StreamConversationEvents")
assert stream["serverStreaming"] is True
assert len(manifest["agentEvents"]["variants"]) == 20
assert len(manifest["http"]["operations"]) == 10
assert len(manifest["sse"]["browserEvents"]) == 21
```

It must additionally:
- reject duplicate `(package, declaration name)` and duplicate package-level enum value symbols;
- require every enum's first value to be number zero;
- require every message field to have exactly `number,name,type,label` plus optional `oneof`;
- reject duplicate field number/name and any label outside `required|optional|repeated`;
- prove every declaration appears in exactly one declared proto file;
- prove every import names a declared file or `google/protobuf/timestamp.proto`;
- prove every consumer file belongs to the declared file set;
- prove every OpenAPI `{path_parameter}` has one exact `in:path` required parameter;
- prove every operation header/query/cookie location is explicit;
- prove `SubmitMessageRequest` has no client message ID or generation field;
- prove only `LaunchRunRequest` has `site_id`/`organization_id` among Agent messages;
- prove Web/root-e2e closures contain no Agent, Model or Capability proto file;
- prove the Web SSE envelope is exactly `event_id,seq,session_id,run_id,timestamp,kind,payload`, with `run_id` mapped from Chat launch ID;
- prove `tool.awaiting_approval` carries Chat interaction identity and the decision payload schema has all five strict arms;
- prove the access-JWT header, exact claim set, issuer/audience, 900-second TTL and stream-expiry deadline;
- prove the fixed 30-day session-cookie cap, omitted-list limit `50`, deterministic first-title rule and stable two-command idempotency;
- prove `RunView` is launch-first with optional pre-admission `agent_run_id`;
- prove every one of the 21 browser kinds has an owner-fact materialization rule and unknown/uncommitted kinds are retention-ineligible.

Run:

```bash
uv run pytest contract/tests/test_slice_a_manifest_authority.py contract/tests/test_slice_a_renderer_contract.py -q
```

Expected: GREEN.

---

### Milestone 3: Render deterministic Protobuf source from the manifest

**Files:**
- Create: `scripts/contract/render_slice_a.py`
- Create: `scripts/contract/__init__.py`
- Create: `scripts/contract/tests/test_render_slice_a.py`
- Modify: `scripts/INDEX.md` to register the contract renderer/checker family, callers and no-network boundary
- Create: `contract/buf.yaml`
- Create: `contract/buf.gen.yaml`
- Create: the nine `.proto` files declared by the manifest

**Step 1: Write renderer RED tests**

Use a temporary output directory. Tests call `render_proto(manifest, output)` twice and assert byte equality. For every declared file, parse rendered text with Buf's descriptor build rather than regex. Mutate one fixture at a time and assert deterministic errors:
- duplicate enum symbol → `ManifestError("duplicate enum symbol ...")`;
- missing declaration assignment → `ManifestError("unassigned declaration ...")`;
- unknown imported type → `ManifestError("unknown protobuf type ...")`;
- invalid oneof label → `ManifestError("oneof field must be required ...")`.

Run:

```bash
uv run pytest scripts/contract/tests/test_render_slice_a.py -q
```

Expected: RED because the renderer is absent.

**Step 2: Implement the exact renderer contract**

`scripts/contract/render_slice_a.py` exports these functions and no network behavior:

```python
class ManifestError(ValueError): ...

def load_manifest(path: Path) -> dict[str, object]: ...
def validate_manifest(manifest: dict[str, object]) -> None: ...
def render_proto(manifest: dict[str, object], output_root: Path) -> list[Path]: ...
def render_openapi(manifest: dict[str, object], output_path: Path) -> Path: ...
def check_tree(manifest_path: Path, expected_root: Path) -> None: ...
```

Rendering rules are fixed:
- `syntax = "proto3";`, then package, sorted declared imports, then declarations in manifest order;
- enum/message/service and field order is manifest order, never alphabetic inference;
- `optional` emits proto3 `optional`; `repeated` emits `repeated`; semantic `required` emits no label;
- oneof fields are emitted inside the named `oneof` in field-number order;
- a method with `serverStreaming:true` emits `returns (stream Response)`; the flag is optional boolean and only `ChatQueryService.StreamConversationEvents` may set it in Slice A;
- fully qualified manifest message/enum types lose only the leading dot in source;
- no validation option/plugin is invented in this barrier;
- each file starts `// GENERATED SOURCE — authority: contract/slice-a-contract-manifest.yaml`;
- writes occur in a temporary sibling and replace the output only after all files validate;
- `--check` renders to a temporary directory and byte-compares without editing.

**Step 3: Add Buf configuration and render**

`contract/buf.yaml` uses `version: v2`, module path `proto` (relative to the config in `contract/`), lint `STANDARD`, and breaking `FILE`. `contract/buf.gen.yaml` uses only local plugin `protoc-gen-es` and Python generation remains in the consumer generator; no remote plugin is permitted.

```bash
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --write
pnpm exec buf format -w contract/proto
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check
pnpm exec buf lint contract
pnpm exec buf build contract -o /tmp/kokoro-slice-a-descriptor.binpb
uv run pytest scripts/contract/tests/test_render_slice_a.py contract/tests/test_slice_a_manifest_authority.py contract/tests/test_slice_a_renderer_contract.py -q
```

Expected: GREEN; formatting followed by renderer `--check` proves renderer emits Buf-canonical bytes.

---

### Milestone 4: Render and independently validate the exact browser OpenAPI

**Files:**
- Create: `contract/openapi/slice-a-web-v1.yaml`
- Create: `contract/tests/test_slice_a_openapi.py`
- Modify: `scripts/contract/render_slice_a.py`

**Step 1: Write the OpenAPI RED test**

The test loads both machine manifest and rendered OpenAPI. It compares exact sets of `(operationId,method,path,status)`, then independently asserts:
- every manifest parameter matches OpenAPI `name/in/required/schema`;
- bodyless operations have no `requestBody`;
- body operations reference their exact strict schema;
- all mutations except logout carry required visible-ASCII `Idempotency-Key` as declared;
- RequestMagicLink body is only email; nonce digest/redirect never appear in browser schema;
- submit body has no generation, command UUID, trusted digest or identity axis;
- decision body is a nonempty array with unique target IDs and strict five-arm payload union;
- SSE response is `text/event-stream`; stale cursor declares `409` common error;
- all JSON objects set `additionalProperties: false`;
- no Hub, Billing, Storage, Project, payment or admin path exists.

Run:

```bash
uv run pytest contract/tests/test_slice_a_openapi.py -q
```

Expected: RED before OpenAPI rendering.

**Step 2: Render, lint and prove parity**

```bash
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --write
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
uv run pytest contract/tests/test_slice_a_openapi.py -q
```

Expected: GREEN. The renderer creates component schemas from `http.schemas`, reusable common error responses and the exact operation parameters; it never guesses location from property names.

---

### Milestone 5: Freeze the first Buf breaking baseline

**Files:**
- Create: `contract/breaking/slice-a-v1.binpb`
- Create: `contract/tests/test_slice_a_descriptor.py`

**Step 1: Compare the real descriptor against the machine manifest**

The test loads `FileDescriptorSet` with `google.protobuf.descriptor_pb2.FileDescriptorSet` and compares:
- exact nine file names/imports/packages;
- every enum/value name and number;
- every message field number/name/type/label/oneof;
- exact service/method input/output types;
- exact `server_streaming` descriptor flag (true only for `ChatQueryService.StreamConversationEvents`);
- absence of undeclared services/messages/enums.

Run before creating the baseline:

```bash
uv run pytest contract/tests/test_slice_a_descriptor.py -q
```

Expected: GREEN against the freshly built `/tmp` descriptor generated inside the test.

**Step 2: Create the immutable first image once**

```bash
test ! -e contract/breaking/slice-a-v1.binpb
pnpm exec buf build contract -o /tmp/kokoro-slice-a-v1.binpb
install -m 0644 /tmp/kokoro-slice-a-v1.binpb contract/breaking/slice-a-v1.binpb
cmp /tmp/kokoro-slice-a-v1.binpb contract/breaking/slice-a-v1.binpb
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
```

Expected: GREEN. Later tasks never overwrite this file.

---

### Milestone 6: Add exact consumer-scoped generation and provenance

**Files:**
- Create: `contract/consumers.yaml`
- Replace: `contract/generate.py`
- Modify: `contract/check.py`
- Create: `contract/tests/test_slice_a_generation.py`
- Modify: `contract/tests/test_generate.py`
- Modify: `contract/README.md`

**Step 1: Write generation RED tests**

Copy `consumerFileClosure` byte-for-byte into `contract/consumers.yaml` and test equality. In temporary clean Git fixtures, assert:
- each consumer receives exactly its declared proto files plus required generated runtime files;
- Web/root-e2e have no Agent/Model/Capability descriptor;
- TypeScript output uses local `node_modules/.bin/protoc-gen-es`; Python uses `uv run python -m grpc_tools.protoc`;
- standard generated Stub/Servicer symbols may coexist in one selected Python file, but an adapter-role architecture test forbids wrong registration;
- generated header records source Root commit and manifest SHA-256;
- provenance records source commit/tree, tool versions, inputs and every output hash;
- same clean commit generates identical bytes twice;
- dirty Root, unknown consumer, extra file and source drift fail closed;
- `--check` reports drift and writes nothing.

Run:

```bash
uv run pytest contract/tests/test_slice_a_generation.py contract/tests/test_generate.py -q
```

Expected: RED against the legacy generator.

**Step 2: Implement committed-tree generation**

The CLI has one exact single-consumer/batch shape; every caller passes the
committed Root explicitly:

```text
python contract/generate.py --source-root ROOT --source-commit SHA (--consumer NAME --repo PATH | --all --repo-map MAP) [--check]
```

It verifies `SHA^{commit}`, reads manifest/proto/OpenAPI/consumer allowlist blobs with `git show`, rejects dirty registered source paths, materializes to a temporary tree, invokes only locked local tools, writes a temporary output, validates hashes and atomically replaces on success. It never follows symlinks, reads child worktrees or stages files.

**Step 3: Prove legacy event/control parity before deletion**

`contract/tests/test_generate.py` compares the old generated Web/Agent event kinds and strict payload field sets against `sse.browserEvents`/AgentEvent in the new manifest. It separately proves magic-link nonce binding, opaque idempotency, RunScope fields, control decision list and stream cursor semantics. Only after this test is GREEN may the barrier commit delete `contract/spec/control.yaml`, `events.yaml`, `http.yaml`, `storage.yaml`, `streams.yaml`; Storage remains future source history, not Slice A output.

Run:

```bash
uv run pytest contract/tests/test_slice_a_generation.py contract/tests/test_generate.py -q
uv run python contract/generate.py --help >/dev/null
```

Expected: GREEN.

---

### Milestone 7: Run the complete Root contract gate and commit the source

**Files:** all Task 1–6 files only.

**Step 1: Run fresh frozen gates**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
pnpm install --frozen-lockfile
uv sync --frozen --group dev
cmp docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check
pnpm exec buf format --diff --exit-code contract/proto
pnpm exec buf lint contract
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
uv run pytest contract/tests scripts/contract/tests -q
git diff --check
```

Expected: every command exits zero.

**Step 2: Independently review the exact cut**

Freeze the worktree. Reviewer checks machine manifest parity, Protobuf scoping/imports, OpenAPI parameter locations, magic-link nonce/redirect binding, method-level caller map, 20 Agent events, mature Web SSE envelope, consumer file closures and generation provenance. Apply findings with a new RED test and rerun Step 1. Do not stage before APPROVE.

**Step 3: Stage an exact allowlist and commit**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
git add -- package.json pnpm-lock.yaml pyproject.toml uv.lock .node-version \
  contract scripts/contract scripts/INDEX.md
git diff --cached --name-only | grep -Ev '^(package.json|pnpm-lock.yaml|pyproject.toml|uv.lock|\.node-version|contract/|scripts/contract/|scripts/INDEX.md$)' && exit 1 || true
git diff --cached --check
git commit -m "feat(contract): freeze Slice A service contracts"
test -z "$(git status --short --untracked-files=no)"
```

Expected: the second clean Root contract-source commit on top of the authority-validation commit. Record its full SHA; all independent backend lanes generate only from this SHA. Do not promote gitlinks in this plan.

---

### Milestone 8: Generate and commit the Root E2E consumer as a descendant output

**Files:**
- Create/replace only the `root-e2e` output paths declared by `contract/consumers.yaml`, including `scripts/e2e/generated/provenance.json`

This is a separate JIT cut after the contract-source commit. In a clean Root checkout, set `ROOT_CONTRACT_COMMIT` to the Milestone 7 SHA and run the exact generator in write mode:

```bash
ROOT_CONTRACT_COMMIT="$(git log -1 --format=%H -- contract)"
uv run --frozen python contract/generate.py \
  --source-root "$(git rev-parse --show-toplevel)" \
  --source-commit "$ROOT_CONTRACT_COMMIT" \
  --consumer root-e2e --repo .
uv run --frozen python contract/generate.py \
  --source-root "$(git rev-parse --show-toplevel)" \
  --source-commit "$ROOT_CONTRACT_COMMIT" \
  --consumer root-e2e --repo . --check
```

Freeze and independently review exact output hashes/provenance, stage only the declared `root-e2e` output closure, and commit `chore(contract): generate Slice A Root E2E client`. The generated provenance must name the Milestone 7 contract-source SHA; the new output commit is never substituted as source provenance. Child consumer generation can proceed in parallel from the same source SHA. Root database and backend E2E gates may use `--check` only after this output commit exists.
