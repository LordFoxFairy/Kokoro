import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  buildSessionEnvironment,
  buildWebEnvironment,
  parseSseFrames,
  sealEnvelope,
  signToken,
} from "./web-session-http-sse.mjs";

const lease = {
  runId: "run_fixture",
  mongo: { database: "kokoro_test_run_fixture" },
  redis: { database: 12 },
};

test("builds isolated child environments from the root lease", () => {
  const session = buildSessionEnvironment(lease, {
    sessionPort: 3901,
    webOrigin: "http://127.0.0.1:3900",
    hubBaseUrl: "http://127.0.0.1:3902",
  });
  assert.equal(session.KOKORO_REDIS_URL, "redis://127.0.0.1:6379/12");
  assert.equal(session.KOKORO_MESSAGE_STORE_MONGO_DB, "kokoro_test_run_fixture");
  assert.equal(session.KOKORO_AUTH_MODE, "hs256");
  assert.equal(session.KOKORO_BILLING_MODE, "off");

  const web = buildWebEnvironment({
    webPort: 3900,
    sessionPort: 3901,
    userBaseUrl: "http://127.0.0.1:3902",
  });
  assert.equal(web.KOKORO_SESSION_BASE_URL, "http://127.0.0.1:3901");
  assert.equal(web.KOKORO_SITE_ID, "site-compatibility");
});

test("creates a verifiable JWT and opaque authenticated web envelope", () => {
  const jwt = signToken("namespace-fixture", 2_000_000_000);
  assert.equal(jwt.split(".").length, 3);
  const cookie = sealEnvelope({
    runtime_jwt: jwt,
    access_exp: 2_000_000_000,
    refresh_token: "refresh-not-real",
    user_id: "user-fixture",
    namespace: "namespace-fixture",
    site_id: "site-compatibility",
    exp: 2_000_000_100,
  });
  assert.equal(cookie.split(".").length, 3);
  assert.equal(cookie.includes("namespace-fixture"), false);
});

test("parses replayed SSE frames and preserves sequence ids", () => {
  const frames = parseSseFrames([
    "id: 2",
    "event: run.created",
    'data: {"seq":2,"kind":"run.created"}',
    "",
    "id: 3",
    "event: message.user",
    'data: {"seq":3,"kind":"message.user"}',
    "",
  ].join("\n"));
  assert.deepEqual(frames.map(({ id, event }) => ({ id, event })), [
    { id: 2, event: "run.created" },
    { id: 3, event: "message.user" },
  ]);
});

test("adapter contains no child compose, legacy container, or database mutation", async () => {
  const source = await readFile(new URL("./web-session-http-sse.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /docker\s+compose|kokoro-dev-|kokoro-platform-mysql|FLUSHDB|dropDatabase/u);
  assert.doesNotMatch(source, /KOKORO_LOCAL_FAKE_MODEL/u);
});
