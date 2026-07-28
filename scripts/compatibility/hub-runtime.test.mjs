import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  AGENT_PROBE_COMMAND,
  ASSERTION_IDS,
  HUB_START_COMMAND,
  SESSION_PROBE_COMMAND,
  buildHubEnvironment,
  buildResult,
  validateLease,
} from "./hub-runtime.mjs";
import { startMembershipFixture } from "./hub-runtime-membership-fixture.mjs";

const lease = {
  schemaVersion: 1,
  runId: "run_fixture",
  endpointFingerprint: "fixture-endpoint",
  resources: ["mysql", "mongo", "redis"],
  mongo: { database: "kokoro_test_run_fixture" },
  redis: {
    database: 8,
    keyPrefix: "kokoro_test_run_fixture:",
    markerKey: "kokoro_test_run_fixture:__lease",
    exclusive: true,
  },
};

test("validates the lease and isolates Hub to its Mongo database", () => {
  assert.deepEqual(validateLease(lease), lease);
  assert.throws(() => validateLease({ ...lease, mongo: { database: "kokoro_hub" } }), /compatibility_scope_invalid/u);
  assert.throws(() => validateLease({ ...lease, resources: ["mongo"] }), /compatibility_scope_invalid/u);

  const env = buildHubEnvironment(lease, {
    hubPort: 43123,
    membershipBaseUrl: "http://127.0.0.1:43124",
    parentEnv: { PATH: "/bin", UNSAFE_PARENT_SECRET: "must-not-flow" },
  });
  assert.equal(env.KOKORO_HUB_MONGO_DB, lease.mongo.database);
  assert.equal(env.KOKORO_HUB_MONGO_URL, "mongodb://127.0.0.1:27017");
  assert.equal(env.KOKORO_USER_BASE_URL, "http://127.0.0.1:43124");
  assert.equal(env.KOKORO_HUB_PORT, "43123");
  assert.equal(env.KOKORO_HUB_MCP_MUTATION, "on");
  assert.equal(env.UNSAFE_PARENT_SECRET, undefined);
});

test("uses only child-owned official consumers and emits the closed assertion set", async () => {
  assert.deepEqual(HUB_START_COMMAND, ["pnpm", "--filter", "@kokoro/hub", "run", "start"]);
  assert.deepEqual(SESSION_PROBE_COMMAND, ["npm", "run", "--silent", "compat:hub-runtime", "--"]);
  assert.deepEqual(AGENT_PROBE_COMMAND.slice(0, 4), ["uv", "run", "--locked", "python"]);
  assert.deepEqual(buildResult(true, 12), {
    schemaVersion: 1,
    scenarioId: "hub-runtime",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: ASSERTION_IDS,
    durationMs: 12,
  });

  const source = await readFile(new URL("./hub-runtime.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /kokoro-(?:agent|platform|session)\/(?:src|test)\//u);
  assert.doesNotMatch(source, /Mongo(?:Mcp|Skill|Secret)|hubCollections|insertOne/u);
  assert.match(source, /\/hub\/self\/mcp\/secrets/u);
});

test("membership fixture verifies Hub caller credentials and returns the public envelope", async () => {
  const fixture = await startMembershipFixture({
    port: 0,
    internalSecret: "fixture-hub-secret",
    namespace: "namespace-fixture",
    userId: "user-fixture",
  });
  try {
    const authorized = await fetch(
      `${fixture.baseUrl}/memberships/check?teamId=namespace-fixture&userId=user-fixture`,
      { headers: {
        "x-kokoro-service": "hub",
        "x-kokoro-internal-secret": "fixture-hub-secret",
      } },
    );
    assert.equal(authorized.status, 200);
    assert.deepEqual(await authorized.json(), { data: { active: true, role: "owner" } });

    const rejected = await fetch(
      `${fixture.baseUrl}/memberships/check?teamId=namespace-fixture&userId=user-fixture`,
      { headers: {
        "x-kokoro-service": "session",
        "x-kokoro-internal-secret": "fixture-hub-secret",
      } },
    );
    assert.equal(rejected.status, 401);

    const nonMember = await fetch(
      `${fixture.baseUrl}/memberships/check?teamId=other&userId=user-fixture`,
      { headers: {
        "x-kokoro-service": "hub",
        "x-kokoro-internal-secret": "fixture-hub-secret",
      } },
    );
    assert.equal(nonMember.status, 200);
    assert.deepEqual(await nonMember.json(), { data: { active: false, role: null } });
  } finally {
    await fixture.close();
  }
});
