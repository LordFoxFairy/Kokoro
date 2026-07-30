import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFile, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { readProtoServiceMethods } from "./check-boundary-registry.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const checker = resolve(here, "check-boundary-registry.mjs");
const repositoryRoot = resolve(here, "../..");
const realSchema = resolve(repositoryRoot, "contract/registry/boundaries.schema.json");

const ERROR_PROTO = `syntax = "proto3";

package kokoro.common.v1;

enum RetryClass {
  RETRY_CLASS_UNSPECIFIED = 0;
  RETRY_CLASS_NEVER = 1;
  RETRY_CLASS_AFTER_DELAY = 2;
  RETRY_CLASS_SAME_IDENTITY = 3;
  RETRY_CLASS_RECONCILE_RECEIPT = 4;
}
`;

// Two HTTP operations, mirroring the shape of contract/spec/http.yaml.
const OPS_YAML = `# fixture
endpoints:
  create_thing:
    method: POST
    path_template: "/things"
  read_thing:
    method: GET
    path_template: "/things/{id}"
`;

const INLINE_OPS_YAML = `# fixture
endpoints:
  create_thing: {method: POST, path_template: "/things"}
  read_thing: {method: GET, path_template: "/things/{id}"}
`;

const OPENAPI_YAML = `openapi: 3.1.0
info:
  title: Fixture
  version: 1.0.0
paths:
  /things:
    post:
      operationId: createThing
  /things/{id}:
    get:
      operationId: readThing
      responses:
        '200':
          description: receipt state
`;

const OPENAPI_FLOW_YAML = `openapi: 3.1.0
info: {title: Fixture, version: 1.0.0}
paths: {"/things": {post: {operationId: createThing}}, "/things/{id}": {get: {operationId: readThing}}}
`;

const OPENAPI_QUOTED_YAML = `openapi: 3.1.0
info: {title: Fixture, version: 1.0.0}
paths:
  "/things":
    "post":
      operationId: "createThing"
  "/things/{id}":
    "get":
      operationId: "readThing"
`;

// A stream registry, mirroring the shape of contract/spec/streams.yaml.
const CHANNELS_YAML = `streams:
  requests:
    name: "kokoro:runs:requests"
  run_events:
    name: "kokoro:run:{run_id}:events"
`;

// A durable command vocabulary that follows object references, like contract/spec/control.yaml.
const COMMANDS_YAML = `objects:
  - name: RuntimeContext
    fields:
      - {name: namespace, type: string_nonempty}
      - {name: session_id, type: string_nonempty}

messages:
  - kind: run.request
    fields:
      - {name: run_id, type: string_nonempty}
      - {name: context, type: object:RuntimeContext}
`;

const SERVICE_PROTO = `syntax = "proto3";

package kokoro.fixture.v1;

service FixtureService {
  rpc DoThing(DoThingRequest) returns (DoThingResponse) {}
  rpc ReadThing(ReadThingRequest) returns (ReadThingResponse) {}
}

message DoThingEffect {
  string site_id = 1;
  string payload = 2;
}

message DoThingRequest {
  DoThingEffect effect = 1;
}

// Buf's canonical inline-empty spelling must not hide the following receipt response.
message EmptyResult {}

message DoThingResponse {
  string id = 1;
  kokoro.common.v1.CommandReceipt receipt = 2;
}

message ReadThingRequest {
  string site_id = 1;
  string command_id = 2;
  string digest_algorithm = 3;
  string request_digest = 4;
}

message ReadThingResponse {
  string id = 1;
  kokoro.common.v1.CommandReceipt receipt = 2;
}
`;

const ROOTS = {
  schemaVersion: 1,
  owners: ["@owner"],
  roots: [
    { id: "service.provider", path: "repo-provider", kind: "boundary", boundary: "service.provider" },
    { id: "service.consumer", path: "repo-consumer", kind: "boundary", boundary: "service.consumer" },
    { id: "provider.component", path: "repo-provider/src", kind: "component", boundary: "service.provider" },
  ],
};

function operation(overrides = {}) {
  return {
    id: "create_thing",
    transport: "http-json",
    effect: true,
    retryClass: "same_identity",
    scope: "site",
    siteBinding: "context-header",
    receipt: { kind: "http-receipt-body", ref: "createThingReceiptSchema" },
    ...overrides,
  };
}

function httpBoundary(overrides = {}) {
  return {
    id: "fixture-http",
    version: 1,
    protocol: "http-json",
    lifecycle: "active",
    trustPlane: "site-bff",
    scope: "site",
    audience: "browser-user",
    provider: { repository: "repo-provider", boundary: "service.provider" },
    consumers: [{ repository: "repo-consumer", boundary: "service.consumer" }],
    failureOwner: "repo-provider",
    deadlineMs: null,
    sourceStatus: "machine-readable",
    sources: [
      {
        kind: "spec-yaml",
        path: "contract/spec/ops.yaml",
        select: { section: "endpoints", member: "mapping-key" },
      },
    ],
    transports: ["http-json"],
    transportSource: null,
    operations: [
      operation(),
      operation({ id: "read_thing", effect: false, retryClass: "after_delay", receipt: null }),
    ],
    ...overrides,
  };
}

function openapiBoundary(overrides = {}) {
  return httpBoundary({
    id: "fixture-openapi",
    sources: [
      {
        kind: "openapi",
        path: "contract/openapi/fixture.yaml",
        select: { member: "operation-id" },
      },
    ],
    operations: [
      operation({ id: "createThing" }),
      operation({ id: "readThing", effect: false, retryClass: "after_delay", receipt: null }),
    ],
    ...overrides,
  });
}

function matrixFor(boundaries) {
  return {
    schemaVersion: 1,
    contracts: boundaries.map((boundary) => ({
      id: boundary.id,
      version: boundary.version,
      providers: [boundary.provider.repository],
      consumers: boundary.consumers.map((consumer) => consumer.repository),
    })),
  };
}

async function write(root, relativePath, contents) {
  const path = join(root, relativePath);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, typeof contents === "string" ? contents : `${JSON.stringify(contents, null, 2)}\n`);
}

/**
 * Build a fixture repository. `boundaries` defaults to one valid HTTP boundary; the compatibility
 * matrix is derived from the same boundaries unless `matrix` overrides it.
 */
async function makeFixture({ boundaries = [httpBoundary()], matrix, roots = ROOTS, files = {} } = {}) {
  const root = await mkdtemp(join(tmpdir(), "kokoro-boundary-"));
  await write(root, "contract/proto/kokoro/common/v1/error.proto", ERROR_PROTO);
  await write(root, "contract/proto/fixture.proto", SERVICE_PROTO);
  await write(root, "contract/spec/ops.yaml", OPS_YAML);
  await write(root, "contract/spec/channels.yaml", CHANNELS_YAML);
  await write(root, "contract/spec/commands.yaml", COMMANDS_YAML);
  await write(root, "contract/openapi/fixture.yaml", OPENAPI_YAML);
  await write(root, "config/architecture/index-roots.yaml", roots);
  await write(root, "config/repository/compatibility-matrix.json", matrix ?? matrixFor(boundaries));
  await write(root, "contract/registry/boundaries.yaml", {
    schemaVersion: 1,
    owners: ["@owner"],
    boundaries,
  });
  await mkdir(join(root, "contract/registry"), { recursive: true });
  await copyFile(realSchema, join(root, "contract/registry/boundaries.schema.json"));
  for (const [path, contents] of Object.entries(files)) await write(root, path, contents);
  return root;
}

function run(root) {
  return spawnSync(process.execPath, [checker, "--root", root], { encoding: "utf8" });
}

async function expectFailure(fixtureOptions, code) {
  const root = await makeFixture(fixtureOptions);
  const result = run(root);
  assert.equal(result.status, 1, `expected failure, got stdout: ${result.stdout}`);
  assert.match(result.stderr, new RegExp(code, "u"));
  return result.stderr;
}

// ------------------------------------------------------------------ happy path

test("accepts a registry whose operations match their contract source", async () => {
  const root = await makeFixture();
  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "boundary_registry_ok: 1 boundaries, 2 operations, 2 header-bound site scopes (migration debt), " +
      "0 declared-only boundaries (no machine-readable source), 0 request-field site scopes, 0 contract-only (published, no provider)\n",
  );
});

test("accepts authoritative mapping keys whose values are inline flow mappings", async () => {
  const root = await makeFixture({ files: { "contract/spec/ops.yaml": INLINE_OPS_YAML } });
  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

test("the shipped registry matches the shipped contract sources", () => {
  const result = spawnSync(process.execPath, [checker, "--root", repositoryRoot], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.match(
    result.stdout,
    /^boundary_registry_ok: \d+ boundaries, \d+ operations, \d+ header-bound site scopes \(migration debt\), \d+ declared-only boundar(?:y|ies) \(no machine-readable source\), \d+ request-field site scopes, \d+ contract-only \(published, no provider\)\n$/u,
  );
});

// ------------------------------------------------------- rule 1: source parity, both directions

test("rejects a source operation missing from the registry", async () => {
  const boundary = httpBoundary();
  boundary.operations = [boundary.operations[0]];
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_operation_orphan: fixture-http: read_thing");
});

test("rejects a registered operation absent from the source", async () => {
  const boundary = httpBoundary();
  boundary.operations.push(operation({ id: "invented_thing" }));
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_operation_undeclared: fixture-http: invented_thing",
  );
});

test("rejects a proto rpc missing from the registry", async () => {
  const boundary = protoBoundary();
  boundary.operations = [boundary.operations[0]];
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_operation_orphan: fixture-proto: ReadThing");
});

test("reads server-streaming proto methods as declared operations", () => {
  const source = `service StreamService {
    rpc Tail(TailRequest) returns (stream TailFrame) {}
}`;
  assert.deepEqual(readProtoServiceMethods(source, "StreamService"), [{
    name: "Tail",
    request: "TailRequest",
    response: "TailFrame",
  }]);
});

test("rejects a registered operation absent from the proto service", async () => {
  const boundary = protoBoundary();
  boundary.operations.push(operation({ id: "InventedRpc", transport: "connect-rpc", scope: "platform", siteBinding: "not-applicable" }));
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_operation_undeclared: fixture-proto: InventedRpc",
  );
});

test("accepts an OpenAPI source whose operationIds exactly match the registry", async () => {
  const boundary = openapiBoundary();
  const root = await makeFixture({ boundaries: [boundary] });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

test("rejects an OpenAPI operationId missing from the registry", async () => {
  const boundary = openapiBoundary();
  boundary.operations = [boundary.operations[0]];
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_operation_orphan: fixture-openapi: readThing",
  );
});

test("rejects a registered operation absent from the OpenAPI descriptor", async () => {
  const boundary = openapiBoundary();
  boundary.operations.push(operation({ id: "inventedThing" }));
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_operation_undeclared: fixture-openapi: inventedThing",
  );
});

test("accepts flow-style OpenAPI parsed by the real YAML loader", async () => {
  const boundary = openapiBoundary();
  const root = await makeFixture({
    boundaries: [boundary],
    files: { "contract/openapi/fixture.yaml": OPENAPI_FLOW_YAML },
  });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

test("accepts quoted OpenAPI path, method, and operationId scalars", async () => {
  const boundary = openapiBoundary();
  const root = await makeFixture({
    boundaries: [boundary],
    files: { "contract/openapi/fixture.yaml": OPENAPI_QUOTED_YAML },
  });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

test("rejects duplicate OpenAPI mapping keys instead of silently overwriting", async () => {
  const duplicate = `openapi: 3.1.0
info: {title: Fixture, version: 1.0.0}
paths:
  /things:
    post:
      operationId: createThing
    post:
      operationId: readThing
`;
  const boundary = openapiBoundary();
  await expectFailure(
    {
      boundaries: [boundary],
      files: { "contract/openapi/fixture.yaml": duplicate },
    },
    "boundary_registry_source_unreadable: duplicate YAML key",
  );
});

test("rejects an OpenAPI operation with no operationId", async () => {
  const missing = `openapi: 3.1.0
info: {title: Fixture, version: 1.0.0}
paths:
  /things:
    post:
      responses: {}
`;
  const boundary = openapiBoundary();
  boundary.operations = [boundary.operations[0]];
  await expectFailure(
    { boundaries: [boundary], files: { "contract/openapi/fixture.yaml": missing } },
    "boundary_registry_source_unreadable: missing operationId",
  );
});

test("rejects a boundary whose source file does not exist", async () => {
  const boundary = httpBoundary();
  boundary.sources[0].path = "contract/spec/absent.yaml";
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_source_missing");
});

test("rejects a boundary that claims machine-readable coverage but ships no source", async () => {
  const boundary = httpBoundary({ sources: [] });
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_source_missing: fixture-http@v1");
});

test("rejects a boundary with no sourceStatus", async () => {
  const boundary = httpBoundary();
  delete boundary.sourceStatus;
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_shape: boundary keys");
});

test("rejects an unknown sourceStatus", async () => {
  const boundary = httpBoundary({ sourceStatus: "probably-fine" });
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_shape: boundary sourceStatus: fixture-http@v1: probably-fine",
  );
});

test("rejects a declared-only boundary that still ships a source", async () => {
  // Otherwise a covered boundary could opt out of the orphan check while keeping its source.
  const boundary = httpBoundary({ sourceStatus: "declared-only" });
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_source_status_mismatch: fixture-http@v1",
  );
});

test("counts a declared-only boundary in the success line and skips its orphan check", async () => {
  // No sources, and operations that match no contract source: the gate must not claim coverage.
  const boundary = httpBoundary({
    sourceStatus: "declared-only",
    sources: [],
    operations: [operation({ id: "anything_at_all" })],
  });
  const root = await makeFixture({ boundaries: [boundary] });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /1 declared-only boundary \(no machine-readable source\)/u);
});

// ----------------------------------------------------------- rule 2: one frozen transport per op

function protoBoundary(overrides = {}) {
  return {
    id: "fixture-proto",
    version: 1,
    protocol: "connect-rpc",
    lifecycle: "active",
    trustPlane: "internal-control",
    scope: "platform",
    audience: "operator",
    provider: { repository: "repo-provider", boundary: "service.provider" },
    consumers: [{ repository: "repo-consumer", boundary: "service.consumer" }],
    failureOwner: "repo-provider",
    deadlineMs: null,
    sourceStatus: "machine-readable",
    sources: [
      { kind: "proto", path: "contract/proto/fixture.proto", select: { service: "FixtureService" } },
    ],
    transports: ["connect-rpc"],
    transportSource: null,
    operations: [
      operation({
        id: "DoThing",
        transport: "connect-rpc",
        scope: "platform",
        siteBinding: "not-applicable",
        receipt: { kind: "command-receipt", ref: "kokoro.common.v1.CommandReceipt" },
      }),
      operation({
        id: "ReadThing",
        transport: "connect-rpc",
        scope: "platform",
        siteBinding: "not-applicable",
        effect: false,
        retryClass: "after_delay",
        receipt: null,
      }),
    ],
    ...overrides,
  };
}

test("rejects a protobuf command receipt ref that is absent from the RPC response", async () => {
  const boundary = protoBoundary();
  boundary.operations[0].receipt.ref = "kokoro.common.v2.CommandReceiptV2";

  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_receipt_unbound: fixture-proto@v1/DoThing: DoThingResponse does not contain kokoro.common.v2.CommandReceiptV2",
  );
});

test("compares protobuf receipt refs by fully-qualified type", async () => {
  const boundary = protoBoundary();
  boundary.operations[0].receipt.ref = "kokoro.common.v2.CommandReceiptV2";
  const source = SERVICE_PROTO.replace(
    "kokoro.common.v1.CommandReceipt receipt = 2;",
    "evil.CommandReceiptV2 receipt = 2;",
  );

  await expectFailure(
    { boundaries: [boundary], files: { "contract/proto/fixture.proto": source } },
    "boundary_registry_receipt_unbound: fixture-proto@v1/DoThing: DoThingResponse does not contain kokoro.common.v2.CommandReceiptV2",
  );
});

test("requires reconcile_receipt to name a reachable non-effect operation", async () => {
  const boundary = protoBoundary();
  boundary.operations[0].retryClass = "reconcile_receipt";

  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_recovery_operation_missing: fixture-proto@v1/DoThing",
  );

  boundary.operations[0].receipt.recoveryOperation = "MissingReceiptRead";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_recovery_operation_unknown: fixture-proto@v1/DoThing: MissingReceiptRead",
  );

  boundary.operations[0].receipt.recoveryOperation = "ReadThing";
  const root = await makeFixture({ boundaries: [boundary] });
  const result = run(root);
  assert.equal(result.status, 0, result.stderr);
});

test("forbids recoveryOperation outside reconcile_receipt", async () => {
  const boundary = protoBoundary();
  boundary.operations[0].receipt.recoveryOperation = "ReadThing";

  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_recovery_operation_forbidden: fixture-proto@v1/DoThing: same_identity",
  );
});

test("rejects a recovery operation without a receipt lookup request and response", async () => {
  const boundary = protoBoundary();
  boundary.operations[0].retryClass = "reconcile_receipt";
  boundary.operations[0].receipt.recoveryOperation = "ReadThing";
  const requestWithoutIdentity = SERVICE_PROTO.replace(
    /message ReadThingRequest \{[\s\S]*?\n\}/u,
    "message ReadThingRequest {\n  string site_id = 1;\n}",
  );
  await expectFailure(
    { boundaries: [boundary], files: { "contract/proto/fixture.proto": requestWithoutIdentity } },
    "boundary_registry_recovery_operation_unbound: fixture-proto@v1/DoThing: ReadThing request",
  );

  const responseWithoutReceipt = SERVICE_PROTO.replace(
    /message ReadThingResponse \{[\s\S]*?\n\}/u,
    "message ReadThingResponse {\n  string id = 1;\n}",
  );
  await expectFailure(
    { boundaries: [boundary], files: { "contract/proto/fixture.proto": responseWithoutReceipt } },
    "boundary_registry_recovery_operation_unbound: fixture-proto@v1/DoThing: ReadThing response",
  );
});

test("requires an OpenAPI state-read recovery operation to be a real successful GET", async () => {
  const boundary = openapiBoundary();
  boundary.operations[0].retryClass = "reconcile_receipt";
  boundary.operations[0].receipt = {
    kind: "state-read",
    recoveryOperation: "readThing",
    ref: "readThing",
  };
  let root = await makeFixture({ boundaries: [boundary] });
  let result = run(root);
  assert.equal(result.status, 0, result.stderr);

  const wrongMethod = OPENAPI_YAML.replace(
    "    get:\n      operationId: readThing",
    "    post:\n      operationId: readThing",
  );
  await expectFailure(
    { boundaries: [boundary], files: { "contract/openapi/fixture.yaml": wrongMethod } },
    "boundary_registry_recovery_operation_unbound: fixture-openapi@v1/createThing: readThing must be GET",
  );

  const noSuccess = OPENAPI_YAML.replace(/\n      responses:[\s\S]*?description: receipt state/u, "");
  await expectFailure(
    { boundaries: [boundary], files: { "contract/openapi/fixture.yaml": noSuccess } },
    "boundary_registry_recovery_operation_unbound: fixture-openapi@v1/createThing: readThing response",
  );
});

test("rejects one consumer reaching the same operation over two transports", async () => {
  // A second authority for create_thing: same consumer, same operation id, different transport.
  const rival = httpBoundary({
    id: "fixture-rival",
    transports: ["connect-rpc"],
    operations: [operation({ transport: "connect-rpc" })],
    sourceStatus: "declared-only",
    sources: [],
  });
  const stderr = await expectFailure(
    { boundaries: [httpBoundary(), rival], matrix: matrixFor([httpBoundary(), rival]) },
    "boundary_registry_transport_conflict: repo-consumer::create_thing",
  );
  assert.match(stderr, /http-json/u);
  assert.match(stderr, /connect-rpc/u);
});

test("rejects an operation transport that the boundary never registered", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].transport = "smoke-signal";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_transport_unregistered: fixture-http@v1/create_thing: smoke-signal",
  );
});

test("rejects a declared transport that is not a real channel in the transport source", async () => {
  const boundary = httpBoundary({
    transports: ["requests", "ghost_stream"],
    transportSource: {
      kind: "spec-yaml",
      path: "contract/spec/channels.yaml",
      select: { section: "streams", member: "mapping-key" },
    },
  });
  boundary.operations[0].transport = "requests";
  boundary.operations[1].transport = "requests";
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_transport_unregistered: fixture-http: ghost_stream");
});

// ------------------------------------------------- rule 3: registry / compatibility matrix parity

test("rejects a matrix contract that the registry never registered", async () => {
  const boundary = httpBoundary();
  const matrix = matrixFor([boundary]);
  matrix.contracts.push({ id: "unregistered-thing", version: 1, providers: ["repo-provider"], consumers: ["repo-consumer"] });
  await expectFailure(
    { boundaries: [boundary], matrix },
    "boundary_registry_matrix_drift: unregistered contract: unregistered-thing@v1",
  );
});

test("rejects a registered boundary that the matrix does not carry", async () => {
  const boundary = httpBoundary();
  await expectFailure(
    { boundaries: [boundary], matrix: { schemaVersion: 1, contracts: [{ id: "other", version: 1, providers: [], consumers: [] }] } },
    "boundary_registry_matrix_drift: contract absent from matrix: fixture-http@v1",
  );
});

test("rejects a provider that disagrees with the matrix", async () => {
  const boundary = httpBoundary();
  const matrix = matrixFor([boundary]);
  matrix.contracts[0].providers = ["repo-consumer"];
  await expectFailure({ boundaries: [boundary], matrix }, "boundary_registry_matrix_drift: providers: fixture-http");
});

test("rejects a consumer that disagrees with the matrix", async () => {
  const boundary = httpBoundary();
  const matrix = matrixFor([boundary]);
  matrix.contracts[0].consumers = ["repo-provider"];
  await expectFailure({ boundaries: [boundary], matrix }, "boundary_registry_matrix_drift: consumers: fixture-http");
});

// -------------------------------------------------- rule 4: parties are registered architecture boundaries

test("rejects a party that is not a registered architecture root", async () => {
  const boundary = httpBoundary();
  boundary.provider.boundary = "service.ghost";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_architecture_boundary_unknown: fixture-http: service.ghost",
  );
});

test("rejects a party that points at a component instead of a boundary", async () => {
  const boundary = httpBoundary();
  boundary.provider.boundary = "provider.component";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_architecture_boundary_unknown: fixture-http: provider.component",
  );
});

test("rejects a party whose architecture boundary lives outside its repository", async () => {
  const boundary = httpBoundary();
  boundary.provider.repository = "repo-consumer";
  const matrix = matrixFor([boundary]);
  await expectFailure(
    { boundaries: [boundary], matrix },
    "boundary_registry_architecture_boundary_unknown: fixture-http: service.provider is not inside repo-consumer",
  );
});

// ------------------------------------------------------- rule 5: retry class comes from the proto

test("rejects a retry class outside the protobuf enum", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].retryClass = "retry_forever";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_retry_class_unknown: fixture-http@v1/create_thing: retry_forever",
  );
});

test("derives allowed retry classes from the proto rather than hardcoding them", async () => {
  // Drop SAME_IDENTITY from the enum; the previously valid registry value must now fail.
  const narrowed = ERROR_PROTO.replace("  RETRY_CLASS_SAME_IDENTITY = 3;\n", "");
  const stderr = await expectFailure(
    { files: { "contract/proto/kokoro/common/v1/error.proto": narrowed } },
    "boundary_registry_retry_class_unknown: fixture-http@v1/create_thing: same_identity",
  );
  // The schema ships the full enum, so narrowing the proto must also trip the drift guard.
  assert.match(stderr, /boundary_registry_schema_drift: retryClass/u);
});

// ------------------------------------------------------------- rule 6: effects must carry receipts

test("rejects an effectful operation with no receipt", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].receipt = null;
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_receipt_missing: fixture-http@v1/create_thing");
});

test("rejects a receipt of an unknown kind", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].receipt = { kind: "vibes", ref: "trust-me" };
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_shape: operation receipt");
});

// --------------------------------------- rules 7 and 9: a request-field site claim must be provable

function siteBoundProtoBoundary() {
  const boundary = protoBoundary({ scope: "site" });
  for (const item of boundary.operations) {
    item.scope = "site";
    item.siteBinding = "request-field";
  }
  return boundary;
}

test("rejects a request-field site claim whose proto request has no site id", async () => {
  // ReadThingRequest carries site_id directly; DoThingRequest only reaches it through
  // DoThingEffect, so stripping that field leaves DoThing's claim unbacked while ReadThing stands.
  const headerOnly = SERVICE_PROTO.replace("  string site_id = 1;\n  string payload = 2;", "  string payload = 2;");
  const stderr = await expectFailure(
    { boundaries: [siteBoundProtoBoundary()], files: { "contract/proto/fixture.proto": headerOnly } },
    "boundary_registry_site_scope_unstructured: fixture-proto/DoThing: DoThingRequest",
  );
  assert.doesNotMatch(stderr, /ReadThing/u);
});

test("accepts a request-field site claim backed by a real proto field", async () => {
  const root = await makeFixture({ boundaries: [siteBoundProtoBoundary()] });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  // A proven claim is not migration debt, so it must not be counted.
  assert.match(result.stdout, /0 header-bound site scopes/u);
});

test("rejects a request-field site claim whose spec YAML source has no site id field", async () => {
  const boundary = httpBoundary();
  for (const item of boundary.operations) item.siteBinding = "request-field";
  const stderr = await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_site_scope_unstructured: fixture-http/create_thing: no site id field in source",
  );
  assert.match(stderr, /fixture-http\/read_thing: no site id field in source/u);
});

test("accepts a request-field site claim backed by a camelCase siteId in spec YAML", async () => {
  // Contract YAML uses snake_case in some files and camelCase in others; both must count.
  const withSite = OPS_YAML.replace(
    "endpoints:",
    "objects:\n  - name: ThingRequest\n    fields:\n      - {name: siteId, type: string_nonempty}\n\nendpoints:",
  );
  const boundary = httpBoundary();
  for (const item of boundary.operations) item.siteBinding = "request-field";
  const root = await makeFixture({ boundaries: [boundary], files: { "contract/spec/ops.yaml": withSite } });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

test("rejects a site-scoped operation that claims no site binding at all", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].siteBinding = "not-applicable";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_site_binding_missing: fixture-http@v1/create_thing",
  );
});

// ------------------------------ rule 11: any remaining header-bound site scopes stay countable

test("counts header-bound site scopes in the success line", async () => {
  const root = await makeFixture();

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /2 header-bound site scopes \(migration debt\)/u);
});

test("reports the real header-bound count for the shipped registry", () => {
  const result = spawnSync(process.execPath, [checker, "--root", repositoryRoot], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  const match = /(\d+) header-bound site scopes/u.exec(result.stdout);
  assert.ok(match, result.stdout);
  // Browser v3 moved its last legacy context-header operations onto the independently verified
  // workload binding. A newly added header-bound operation must not silently recreate that debt.
  assert.equal(Number(match[1]), 0, "shipped registry must not reintroduce header-bound Site authority");
});

// --------------------------------------------------------- rule 8: the GA namespace axis stays clean

test("rejects a site-scoped operation on a namespace boundary", async () => {
  const boundary = httpBoundary({ scope: "namespace" });
  boundary.operations[0].scope = "site";
  boundary.operations[1].scope = "namespace";
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_namespace_axis_polluted: fixture-http/create_thing: site scope",
  );
});

test("rejects a namespace operation that claims a request-field site binding", async () => {
  const boundary = httpBoundary({ scope: "namespace" });
  for (const item of boundary.operations) {
    item.scope = "namespace";
    item.siteBinding = "request-field";
  }
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_namespace_axis_polluted: fixture-http@v1/create_thing: siteBinding request-field",
  );
});

test("rejects a namespace operation that claims a header site binding", async () => {
  const boundary = httpBoundary({ scope: "namespace" });
  for (const item of boundary.operations) item.scope = "namespace";
  // siteBinding stays context-header from the base fixture: still a Site axis on the GA wire.
  await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_namespace_axis_polluted: fixture-http@v1/create_thing: siteBinding context-header",
  );
});

test("rejects a second identity axis in a namespace proto request", async () => {
  const boundary = protoBoundary({ scope: "namespace" });
  for (const item of boundary.operations) item.scope = "namespace";
  const stderr = await expectFailure(
    { boundaries: [boundary] },
    "boundary_registry_namespace_axis_polluted: fixture-proto/DoThing: DoThingRequest.site_id",
  );
  assert.match(stderr, /fixture-proto\/ReadThing: ReadThingRequest\.site_id/u);
});

test("rejects a second identity axis reached through a nested durable command object", async () => {
  // owner_id is added to RuntimeContext, which run.request only reaches via `object:RuntimeContext`.
  const polluted = COMMANDS_YAML.replace(
    "      - {name: session_id, type: string_nonempty}",
    "      - {name: session_id, type: string_nonempty}\n      - {name: owner_id, type: string_nonempty}",
  );
  const boundary = httpBoundary({
    scope: "namespace",
    sources: [
      {
        kind: "spec-yaml",
        path: "contract/spec/commands.yaml",
        select: { section: "messages", member: "field", field: "kind" },
      },
    ],
    transports: ["requests"],
    operations: [operation({ id: "run.request", transport: "requests", scope: "namespace", siteBinding: "not-applicable" })],
  });
  await expectFailure(
    { boundaries: [boundary], files: { "contract/spec/commands.yaml": polluted } },
    "boundary_registry_namespace_axis_polluted: fixture-http: contract/spec/commands.yaml: owner_id",
  );
});

test("accepts a namespace boundary whose durable command carries only namespace", async () => {
  const boundary = httpBoundary({
    scope: "namespace",
    sources: [
      {
        kind: "spec-yaml",
        path: "contract/spec/commands.yaml",
        select: { section: "messages", member: "field", field: "kind" },
      },
    ],
    transports: ["requests"],
    operations: [operation({ id: "run.request", transport: "requests", scope: "namespace", siteBinding: "not-applicable" })],
  });
  const root = await makeFixture({ boundaries: [boundary] });

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
});

// ------------------------------------------------------------------------ structure and drift

test("rejects a duplicate boundary id", async () => {
  const boundaries = [httpBoundary(), httpBoundary()];
  await expectFailure({ boundaries, matrix: matrixFor([httpBoundary()]) }, "boundary_registry_duplicate_boundary: fixture-http");
});

test("rejects a duplicate operation id inside one boundary", async () => {
  const boundary = httpBoundary();
  boundary.operations.push(operation());
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_duplicate_operation: fixture-http@v1/create_thing");
});

test("rejects an unknown scope", async () => {
  const boundary = httpBoundary();
  boundary.operations[0].scope = "galaxy";
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_shape: operation scope");
});

test("rejects an unexpected boundary key", async () => {
  const boundary = httpBoundary();
  boundary.notes = "should not be here";
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_shape: boundary keys");
});

test("rejects a schema whose enums drift from the gate", async () => {
  const root = await makeFixture();
  const schemaPath = join(root, "contract/registry/boundaries.schema.json");
  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  schema.$defs.scope.enum = ["site", "platform"];
  await writeFile(schemaPath, JSON.stringify(schema, null, 2));

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /boundary_registry_schema_drift: scope enum/u);
});

test("rejects an unreadable registry", async () => {
  const root = await makeFixture();
  await writeFile(join(root, "contract/registry/boundaries.yaml"), "{ not json");

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /boundary_registry_json/u);
});

test("rejects unknown arguments", () => {
  const result = spawnSync(process.execPath, [checker, "--sideload", "x"], { encoding: "utf8" });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /boundary_registry_arguments_invalid/u);
});

test("rejects a boundary with no lifecycle", async () => {
  const boundary = httpBoundary();
  delete boundary.lifecycle;
  await expectFailure({ boundaries: [boundary] }, "boundary_registry_shape: boundary keys");
});

test("rejects an unknown lifecycle", async () => {
  await expectFailure(
    { boundaries: [httpBoundary({ lifecycle: "someday" })] },
    "boundary_registry_shape: boundary lifecycle: fixture-http@v1: someday",
  );
});

test("a contract-only boundary must stay out of the compatibility matrix", async () => {
  // The matrix drives the runtime gate, so listing a protocol with no provider
  // there would assert a capability that does not exist.
  await expectFailure(
    { boundaries: [httpBoundary({ lifecycle: "contract-only" })] },
    "boundary_registry_matrix_drift: contract-only boundary in matrix: fixture-http",
  );
});

test("one object's siteId does not vouch for a sibling operation that lacks it", async () => {
  // Object-derived operation ids can be proved individually. Checking the file as a
  // whole previously let any single siteId clear every operation in the source.
  const yaml = [
    "objects:",
    "  - name: AlphaRequest",
    "    fields:",
    "      - {name: siteId, type: string_nonempty}",
    "  - name: BetaRequest",
    "    fields:",
    "      - {name: other, type: string_nonempty}",
    "",
  ].join("\n");
  const boundary = httpBoundary({
    sources: [
      {
        kind: "spec-yaml",
        path: "contract/spec/ops.yaml",
        select: { section: "objects", member: "field", field: "name", match: "^(.+?)Request$", case: "snake" },
      },
    ],
    operations: [
      { id: "alpha", transport: "http-json", effect: false, retryClass: "after_delay", scope: "site", siteBinding: "request-field", receipt: null },
      { id: "beta", transport: "http-json", effect: false, retryClass: "after_delay", scope: "site", siteBinding: "request-field", receipt: null },
    ],
  });
  const root = await makeFixture({ boundaries: [boundary], files: { "contract/spec/ops.yaml": yaml } });

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /site_scope_unstructured: fixture-http\/beta/u);
  assert.doesNotMatch(result.stderr, /site_scope_unstructured: fixture-http\/alpha/u);
});
