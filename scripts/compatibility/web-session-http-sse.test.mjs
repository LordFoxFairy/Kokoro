import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import * as adapter from "./web-session-http-sse.mjs";

const {
  buildSessionEnvironment,
  buildWebEnvironment,
  parseSseFrames,
  sealEnvelope,
  signToken,
} = adapter;

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
    siteBaseUrl: "http://127.0.0.1:3902",
  });
  assert.equal(web.KOKORO_SESSION_BASE_URL, "http://127.0.0.1:3901");
  assert.equal(web.KOKORO_SITE_ID, "site-compatibility");
  assert.equal(web.KOKORO_SITE_BASE_URL, "http://127.0.0.1:3902");
  assert.equal(web.KOKORO_SITE_ALLOW_DEV_FALLBACK, "false");
  assert.equal(web.KOKORO_SITE_STRICT, "true");
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
    "",
  ].join("\n"));
  assert.deepEqual(frames.map(({ id, event }) => ({ id, event })), [
    { id: 2, event: "run.created" },
    { id: 3, event: "message.user" },
  ]);
});

test("does not parse an unterminated SSE frame", () => {
  assert.deepEqual(parseSseFrames('id: 2\nevent: run.created\ndata: {"seq":2}'), []);
  assert.deepEqual(
    parseSseFrames('id: 2\nevent: run.created\ndata: {"seq":2}\n\nid: 3\nevent: message.user'),
    [{ id: 2, event: "run.created", data: { seq: 2 } }],
  );
});

test("consumes SSE frames across one-byte and multi-chunk boundaries without losing the tail", () => {
  assert.equal(typeof adapter.consumeSseFrames, "function");
  const source = [
    "id: 2",
    "event: run.created",
    'data: {"seq":2,"kind":"run.created"}',
    "",
    "id: 3",
    "event: message.user",
    'data: {"seq":3,"kind":"message.user"}',
    "",
    "",
  ].join("\n");

  let tail = "";
  const bytewise = [];
  for (const character of source) {
    const consumed = adapter.consumeSseFrames(`${tail}${character}`);
    bytewise.push(...consumed.frames);
    tail = consumed.tail;
  }
  assert.deepEqual(bytewise.map(({ id }) => id), [2, 3]);
  assert.equal(tail, "");

  const chunks = [source.slice(0, 47), source.slice(47, 51), source.slice(51, -1), source.slice(-1)];
  tail = "";
  const chunked = [];
  for (const chunk of chunks) {
    const consumed = adapter.consumeSseFrames(`${tail}${chunk}`);
    chunked.push(...consumed.frames);
    tail = consumed.tail;
  }
  assert.deepEqual(chunked.map(({ id }) => id), [2, 3]);
  assert.equal(tail, "");
});

test("controlled fixture resolves only the bound Host and keeps Hub resolution route-scoped", async () => {
  assert.equal(typeof adapter.startBoundaryFixture, "function");
  const fixture = await adapter.startBoundaryFixture({ siteHost: "site.compat.test" });
  const webHeaders = {
    "x-kokoro-service": "web-bff",
    "x-kokoro-internal-secret": "compatibility-web-not-real",
  };
  const sessionHeaders = {
    "x-kokoro-service": "session",
    "x-kokoro-internal-secret": "compatibility-session-not-real",
  };
  try {
    const resolved = await fetch(`${fixture.baseUrl}/site-context/resolve?host=site.compat.test`, {
      headers: webHeaders,
    });
    assert.equal(resolved.status, 200);
    assert.deepEqual((await resolved.json()).data.context, {
      siteId: "site-compatibility",
      siteKey: "compatibility",
      host: "site.compat.test",
      defaultLocale: "en",
      timezone: "UTC",
      brand: { name: "Compatibility", logoUrl: null, themeColor: null },
    });

    const unknownSite = await fetch(`${fixture.baseUrl}/site-context/resolve?host=unknown.test`, {
      headers: webHeaders,
    });
    assert.equal(unknownSite.status, 404);
    assert.equal((await unknownSite.json()).error.code, "site_context.not_found");

    const untrustedSite = await fetch(`${fixture.baseUrl}/site-context/resolve?host=site.compat.test`);
    assert.equal(untrustedSite.status, 401);
    assert.equal((await untrustedSite.json()).error.code, "fixture.unauthorized");

    const hub = await fetch(
      `${fixture.baseUrl}/hub/runtime/resolve?namespace=namespace-compatibility`,
      { headers: sessionHeaders },
    );
    assert.equal(hub.status, 200);
    assert.deepEqual(await hub.json(), { data: { skills: [], mcp_servers: [] } });

    const unknownRoute = await fetch(`${fixture.baseUrl}/unknown`, { headers: sessionHeaders });
    assert.equal(unknownRoute.status, 404);
    assert.equal((await unknownRoute.json()).error.code, "fixture.route_not_found");

    assert.deepEqual(fixture.requests, [
      { method: "GET", pathname: "/site-context/resolve", caller: "web-bff", host: "site.compat.test", namespace: null },
      { method: "GET", pathname: "/site-context/resolve", caller: "web-bff", host: "unknown.test", namespace: null },
      { method: "GET", pathname: "/site-context/resolve", caller: null, host: "site.compat.test", namespace: null },
      { method: "GET", pathname: "/hub/runtime/resolve", caller: "session", host: null, namespace: "namespace-compatibility" },
      { method: "GET", pathname: "/unknown", caller: "session", host: null, namespace: null },
    ]);
  } finally {
    await fixture.close();
  }
});

test("readiness fails fast on deterministic HTTP rejection and child exit", async () => {
  assert.equal(typeof adapter.waitHttp, "function");
  let calls = 0;
  await assert.rejects(
    adapter.waitHttp("http://service.test/probe", {
      phase: "web",
      accept: [401],
      child: { pid: 123, exitCode: null, signalCode: null },
      fetchImpl: async () => {
        calls += 1;
        return new Response(null, { status: 404 });
      },
      sleep: async () => {},
    }),
    (error) => error?.reasonCode === "web_readiness_http_404",
  );
  assert.equal(calls, 1);

  calls = 0;
  await assert.rejects(
    adapter.waitHttp("http://service.test/probe", {
      phase: "session",
      accept: [401],
      child: { pid: 123, exitCode: 1, signalCode: null },
      fetchImpl: async () => {
        calls += 1;
        return new Response(null, { status: 401 });
      },
      sleep: async () => {},
    }),
    (error) => error?.reasonCode === "session_readiness_child_exited",
  );
  assert.equal(calls, 0);
});

test("readiness retries transient failures and reports the sanitized last HTTP status", async () => {
  let calls = 0;
  const response = await adapter.waitHttp("http://service.test/probe", {
    phase: "session",
    accept: [401],
    child: { pid: 123, exitCode: null, signalCode: null },
    fetchImpl: async () => {
      calls += 1;
      return new Response(null, { status: calls === 1 ? 503 : 401 });
    },
    sleep: async () => {},
  });
  assert.equal(response.status, 401);
  assert.equal(calls, 2);

  let now = 0;
  await assert.rejects(
    adapter.waitHttp("http://service.test/probe", {
      phase: "web",
      accept: [401],
      timeoutMs: 1,
      child: { pid: 123, exitCode: null, signalCode: null },
      fetchImpl: async () => new Response(null, { status: 503 }),
      sleep: async () => { now += 2; },
      now: () => now,
    }),
    (error) => error?.reasonCode === "web_readiness_timeout_http_503",
  );
});

test("machine result advertises Host-to-Site binding as a first-class assertion", () => {
  assert.equal(typeof adapter.buildResult, "function");
  const result = adapter.buildResult("pass", "ok", 12);
  assert.equal(result.outcome, "pass");
  assert.ok(result.assertionIds.includes("web-session:site-binding"));
});

test("adapter contains no child compose, legacy container, or database mutation", async () => {
  const source = await readFile(new URL("./web-session-http-sse.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /docker\s+compose|kokoro-dev-|kokoro-platform-mysql|FLUSHDB|dropDatabase/u);
  assert.doesNotMatch(source, /KOKORO_LOCAL_FAKE_MODEL/u);
});
