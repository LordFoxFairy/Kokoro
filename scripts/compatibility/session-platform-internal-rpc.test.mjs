import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { readFile } from "node:fs/promises";
import test from "node:test";

const adapter = await import("./session-platform-internal-rpc.mjs");

const lease = {
  schemaVersion: 1,
  runId: "run_fixture",
  endpointFingerprint: "kokoro-infra.local",
  resources: ["mongo", "mysql", "redis"],
  leaseToken: "a".repeat(64),
  createdAt: "2026-07-27T00:00:00.000Z",
  mysql: {
    site: "kokoro_test_run_fixture_site",
    user: "kokoro_test_run_fixture_user",
    model: "kokoro_test_run_fixture_model",
    credit: "kokoro_test_run_fixture_credit",
    payment: "kokoro_test_run_fixture_payment",
    admin: "kokoro_test_run_fixture_admin",
  },
  mysqlUsers: Object.fromEntries(
    ["site", "user", "model", "credit", "payment", "admin"].map((context) => [
      context,
      { username: `kt_${context}_fixture`, password: `${context}-password-not-real` },
    ]),
  ),
  mongo: { database: "kokoro_test_run_fixture" },
  redis: {
    database: 12,
    keyPrefix: "kokoro_test_run_fixture:",
    markerKey: "kokoro_test_run_fixture:__lease",
    exclusive: true,
  },
};

test("validates the selected root MySQL, Mongo, and Redis lease", () => {
  assert.equal(adapter.validateLease(lease), lease);

  for (const invalid of [
    { ...lease, resources: ["mongo", "redis"] },
    { ...lease, mysql: { ...lease.mysql, model: "kokoro" } },
    { ...lease, mysqlUsers: { ...lease.mysqlUsers, model: { username: "root", password: "pw" } } },
    { ...lease, mongo: { database: "kokoro" } },
    { ...lease, redis: { ...lease.redis, database: 0 } },
    { ...lease, redis: { ...lease.redis, exclusive: false } },
  ]) {
    assert.throws(() => adapter.validateLease(invalid), /compatibility_scope_invalid/u);
  }
});

test("assembles isolated child environments without inheriting parent credentials", () => {
  const parent = {
    PATH: "/example/bin",
    LANG: "en_US.UTF-8",
    HOME: "/sensitive/home",
    DATABASE_URL_MODEL: "mysql://parent-secret",
    KOKORO_INTERNAL_SECRET_SESSION: "parent-secret",
    OPENAI_API_KEY: "parent-secret",
  };
  const model = adapter.buildModelEnvironment(lease, { modelPort: 4229, parentEnv: parent });
  const session = adapter.buildSessionEnvironment(lease, {
    sessionPort: 3019,
    modelBaseUrl: "http://127.0.0.1:4229",
    parentEnv: parent,
  });

  assert.equal(model.PATH, "/example/bin");
  assert.equal(model.LANG, "en_US.UTF-8");
  assert.equal(model.HOME, undefined);
  assert.equal(model.OPENAI_API_KEY, undefined);
  assert.equal(model.KOKORO_MODEL_PORT, "4229");
  const databaseUrl = new URL(model.DATABASE_URL_MODEL);
  assert.equal(databaseUrl.hostname, "127.0.0.1");
  assert.equal(databaseUrl.port, "3307");
  assert.equal(databaseUrl.pathname, "/kokoro_test_run_fixture_model");
  assert.equal(databaseUrl.username, lease.mysqlUsers.model.username);
  assert.equal(databaseUrl.password, lease.mysqlUsers.model.password);
  assert.notEqual(model.KOKORO_INTERNAL_SECRET_SESSION, "parent-secret");

  assert.equal(session.PATH, "/example/bin");
  assert.equal(session.HOME, undefined);
  assert.equal(session.OPENAI_API_KEY, undefined);
  assert.equal(session.KOKORO_REDIS_URL, "redis://127.0.0.1:6379/12");
  assert.equal(session.KOKORO_MESSAGE_STORE_MONGO_DB, "kokoro_test_run_fixture");
  assert.equal(session.KOKORO_MODEL_BASE_URL, "http://127.0.0.1:4229");
  assert.equal(session.KOKORO_BILLING_MODE, "shadow");
  assert.equal(session.KOKORO_SITE_ID, "site-compatibility");
  assert.equal(session.KOKORO_INTERNAL_SECRET_SESSION, model.KOKORO_INTERNAL_SECRET_SESSION);
});

test("builds the real HS256 bearer and per-caller Platform header contract", () => {
  const token = adapter.signToken("namespace-compatibility", 2_000_000_000);
  const [head, body, signature] = token.split(".");
  assert.equal(JSON.parse(Buffer.from(head, "base64url").toString()).alg, "HS256");
  assert.deepEqual(JSON.parse(Buffer.from(body, "base64url").toString()), {
    sub: "namespace-compatibility",
    exp: 2_000_000_000,
  });
  assert.equal(
    signature,
    createHmac("sha256", adapter.AUTH_SECRET).update(`${head}.${body}`).digest("base64url"),
  );
  assert.deepEqual(adapter.platformRequestHeaders(), {
    "x-kokoro-service": "session",
    "x-kokoro-internal-secret": adapter.INTERNAL_SECRET,
    "x-kokoro-site-id": "site-compatibility",
  });
});

test("emits the fixed closed machine result schema with bounded duration", () => {
  assert.deepEqual(adapter.buildResult(true, Number.MAX_SAFE_INTEGER), {
    schemaVersion: 1,
    scenarioId: "session-platform-internal-rpc",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: [
      "session-platform:session-model-catalog",
      "session-platform:platform-binding-resolve",
      "session-platform:missing-caller-rejected",
      "session-platform:wrong-caller-rejected",
      "session-platform:session-caller-authorized",
      "session-platform:catalogue-unscoped-rejected",
      "session-platform:catalogue-scoped-authorized",
    ],
    durationMs: 179_999,
  });
  assert.equal(adapter.buildResult(false, -10).durationMs, 0);
  assert.equal(adapter.buildResult(false, 42).reasonCode, "session_platform_live_failed");
});

test("adapter source cannot use child compose, private database access, env files, or observable logs", async () => {
  const source = await readFile(new URL("./session-platform-internal-rpc.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /docker(?:\s+compose)?|compose\.ya?ml/iu);
  assert.doesNotMatch(
    source,
    /(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE\s+TABLE)\s+[^"'`\n]*(?:model_|session_|message_|run_)/iu,
  );
  assert.doesNotMatch(source, /(?:readFile|dotenv|--env-file)[^\n]*\.env/iu);
  assert.doesNotMatch(source, /console\.(?:log|error|warn)|process\.(?:stdout|stderr)\.write/u);
  assert.match(source, /detached:\s*true/u);
  assert.match(source, /process\.kill\(-child\.pid/u);
  assert.match(source, /finally\s*\{[\s\S]*stopAll/u);
  assert.match(source, /writeSync\(3,/u);
});
