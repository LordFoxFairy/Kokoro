import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  AGENT_PROBE_COMMAND,
  ASSERTION_IDS,
  HUB_CONNECT_START_COMMAND,
  HUB_HTTP_START_COMMAND,
  PLATFORM_FIXTURE_COMMAND,
  buildConnectEnvironment,
  buildHttpEnvironment,
  buildResult,
  validateLease,
} from "./hub-runtime.mjs";

const lease = {
  schemaVersion: 1,
  runId: "run_fixture",
  endpointFingerprint: "fixture-endpoint",
  resources: ["postgres", "mongo", "redis"],
  postgres: { database: "kokoro_test_run_fixture" },
  mongo: { database: "kokoro_test_run_fixture" },
  redis: {
    database: 8,
    keyPrefix: "kokoro_test_run_fixture:",
    markerKey: "kokoro_test_run_fixture:__lease",
    exclusive: true,
  },
};

test("validates the lease and isolates both Hub provider processes to its Mongo database", () => {
  assert.deepEqual(validateLease(lease), lease);
  assert.throws(() => validateLease({ ...lease, mongo: { database: "kokoro_hub" } }), /compatibility_scope_invalid/u);
  assert.throws(() => validateLease({ ...lease, resources: ["postgres", "redis"] }), /compatibility_scope_invalid/u);

  const http = buildHttpEnvironment(lease, {
    port: 43123,
    workspaceConfig: "/tmp/workspace.yaml",
    parentEnv: { PATH: "/bin", UNSAFE_PARENT_SECRET: "must-not-flow" },
  });
  assert.equal(http.KOKORO_HUB_MONGO_DB, lease.mongo.database);
  assert.equal(http.KOKORO_HUB_MONGO_URL, "mongodb://127.0.0.1:27017/?directConnection=true");
  assert.equal(http.KOKORO_HUB_PORT, "43123");
  assert.equal(http.KOKORO_WORKSPACE_CONFIG, "/tmp/workspace.yaml");
  assert.equal(http.UNSAFE_PARENT_SECRET, undefined);

  const connect = buildConnectEnvironment(lease, {
    port: 43124,
    projectionPort: 43125,
    workspaceConfig: "/tmp/workspace.yaml",
    trust: {
      ca: "/tmp/ca.pem",
      serverCert: "/tmp/server.pem",
      serverKey: "/tmp/server-key.pem",
      platformCert: "/tmp/platform.pem",
      platformKey: "/tmp/platform-key.pem",
      peers: "/tmp/peers.json",
      signingKey: "/tmp/signing.pem",
    },
    parentEnv: { PATH: "/bin", UNSAFE_PARENT_SECRET: "must-not-flow" },
  });
  assert.equal(connect.KOKORO_HUB_MONGO_DB, lease.mongo.database);
  assert.equal(connect.KOKORO_HUB_MONGO_URL, "mongodb://127.0.0.1:27017/?directConnection=true");
  assert.equal(connect.KOKORO_HUB_CONNECT_PORT, "43124");
  assert.equal(connect.KOKORO_HUB_PLATFORM_PROJECTION_BASE_URL, "https://localhost:43125");
  assert.equal(connect.KOKORO_HUB_RUNTIME_AGENT_CALLER_SAN_URI, "spiffe://kokoro.internal/agent");
  assert.equal(connect.UNSAFE_PARENT_SECRET, undefined);
});

test("runs the production Hub providers and Agent consumer with a closed assertion set", async () => {
  assert.deepEqual(HUB_HTTP_START_COMMAND, ["pnpm", "--filter", "@kokoro/hub", "run", "dev"]);
  assert.deepEqual(HUB_CONNECT_START_COMMAND, ["pnpm", "--filter", "@kokoro/hub", "run", "dev:connect"]);
  assert.deepEqual(PLATFORM_FIXTURE_COMMAND.slice(0, 3), ["pnpm", "exec", "tsx"]);
  assert.deepEqual(AGENT_PROBE_COMMAND.slice(0, 4), ["uv", "run", "--locked", "python"]);
  assert.deepEqual(buildResult(true, 12), {
    schemaVersion: 1,
    scenarioId: "hub-runtime",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: ASSERTION_IDS,
    durationMs: 12,
  });

  const [runner, platformFixture, agentProbe] = await Promise.all([
    readFile(new URL("./hub-runtime.mjs", import.meta.url), "utf8"),
    readFile(new URL("./hub-runtime-platform-fixture.mts", import.meta.url), "utf8"),
    readFile(new URL("./hub_runtime_agent.py", import.meta.url), "utf8"),
  ]);
  assert.doesNotMatch(`${runner}\n${platformFixture}\n${agentProbe}`, /ResolveMcpSecrets|KOKORO_HUB_BASE_URL|kokoro-session/u);
  assert.doesNotMatch(`${runner}\n${platformFixture}`, /insertOne|updateOne|MongoClient/u);
  assert.doesNotMatch(runner, /copy_extensions/u);
  assert.match(runner, /"-extfile", extensions/u);
  assert.doesNotMatch(runner, /"genpkey"/u);
  assert.match(runner, /generateKeyPairSync\("ed25519"\)/u);
  assert.match(runner, /request\.once\("error", fail\)/u);
  assert.match(platformFixture, /HubCatalogService/u);
  assert.match(platformFixture, /create\(FreezeCatalogEffectSchema/u);
  assert.match(agentProbe, /HubExecutionAssemblyClient/u);
  assert.match(agentProbe, /read_body/u);
});
