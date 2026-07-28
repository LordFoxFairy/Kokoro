#!/usr/bin/env node

import { createCipheriv, createHash, createHmac, randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { writeSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer as createHttpServer, request as httpRequest } from "node:http";
import { createServer as createNetServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const AUTH_SECRET = "compatibility-hs256-not-real";
const WEB_SECRET = "compatibility-envelope-not-real";
const SITE_ID = "site-compatibility";
const SITE_HOST = "127.0.0.1";
const NAMESPACE = "namespace-compatibility";
const WEB_INTERNAL_SECRET = "compatibility-web-not-real";
const SESSION_INTERNAL_SECRET = "compatibility-session-not-real";
const READINESS_PHASES = new Set(["session", "web"]);
const AUTHORITY_PROBE_MAX_BYTES = 64 * 1024;
const children = new Set();

class ScenarioFailure extends Error {
  constructor(reasonCode) {
    super(reasonCode);
    this.name = "ScenarioFailure";
    this.reasonCode = reasonCode;
  }
}

function fail(reasonCode) {
  throw new ScenarioFailure(reasonCode);
}

function encodeJson(value) {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function signToken(subject, expiresAt) {
  const header = encodeJson({ alg: "HS256", typ: "JWT" });
  const body = encodeJson({ sub: subject, exp: expiresAt });
  const signature = createHmac("sha256", AUTH_SECRET)
    .update(`${header}.${body}`)
    .digest("base64url");
  return `${header}.${body}.${signature}`;
}

function sealEnvelope(payload) {
  const key = createHash("sha256").update(WEB_SECRET, "utf8").digest();
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([
    cipher.update(Buffer.from(JSON.stringify(payload), "utf8")),
    cipher.final(),
  ]);
  return [iv, ciphertext, cipher.getAuthTag()].map((part) => part.toString("base64url")).join(".");
}

function validateLease(value) {
  if (
    value === null ||
    typeof value !== "object" ||
    !/^run_[a-z0-9][a-z0-9_-]{2,31}$/u.test(value.runId ?? "") ||
    typeof value.mongo?.database !== "string" ||
    !value.mongo.database.startsWith("kokoro_test_") ||
    !Number.isInteger(value.redis?.database) ||
    value.redis.database < 8 ||
    value.redis.database > 15
  ) {
    throw new Error("compatibility_scope_invalid");
  }
  return value;
}

function buildSessionEnvironment(lease, { sessionPort, webOrigin, hubBaseUrl }) {
  return {
    KOKORO_SESSION_PORT: String(sessionPort),
    KOKORO_REDIS_URL: `redis://127.0.0.1:6379/${lease.redis.database}`,
    KOKORO_MESSAGE_STORE_MONGO_URL: "mongodb://127.0.0.1:27017",
    KOKORO_MESSAGE_STORE_MONGO_DB: lease.mongo.database,
    KOKORO_WEB_ORIGIN: webOrigin,
    KOKORO_AUTH_MODE: "hs256",
    KOKORO_AUTH_JWT_SECRET: AUTH_SECRET,
    KOKORO_HUB_BASE_URL: hubBaseUrl,
    KOKORO_INTERNAL_SECRET_SESSION: SESSION_INTERNAL_SECRET,
    KOKORO_BILLING_MODE: "off",
    KOKORO_WORKSPACE_ROOT: resolve(root, "tmp/compatibility-workspaces", lease.runId),
  };
}

function buildWebEnvironment({ sessionPort, userBaseUrl, siteBaseUrl }) {
  return {
    KOKORO_WEB_SESSION_SECRET: WEB_SECRET,
    KOKORO_USER_BASE_URL: userBaseUrl,
    KOKORO_SESSION_BASE_URL: `http://127.0.0.1:${sessionPort}`,
    KOKORO_SITE_BASE_URL: siteBaseUrl,
    KOKORO_SITE_ID: SITE_ID,
    KOKORO_SITE_ALLOW_DEV_FALLBACK: "false",
    KOKORO_SITE_STRICT: "true",
    KOKORO_INTERNAL_SECRET_WEB_BFF: WEB_INTERNAL_SECRET,
  };
}

function parseSseBlock(block) {
  const fields = new Map();
  const data = [];
  for (const line of block.split(/\r?\n/u)) {
    if (line.length === 0 || line.startsWith(":")) continue;
    const separator = line.indexOf(":");
    const name = separator < 0 ? line : line.slice(0, separator);
    const rawValue = separator < 0 ? "" : line.slice(separator + 1);
    const value = rawValue.startsWith(" ") ? rawValue.slice(1) : rawValue;
    if (name === "data") data.push(value);
    else fields.set(name, value);
  }
  if (data.length === 0) return null;
  return {
    id: Number(fields.get("id")),
    event: fields.get("event"),
    data: JSON.parse(data.join("\n")),
  };
}

function consumeSseFrames(source) {
  const frames = [];
  const boundary = /\r?\n\r?\n/gu;
  let cursor = 0;
  for (let match = boundary.exec(source); match !== null; match = boundary.exec(source)) {
    const parsed = parseSseBlock(source.slice(cursor, match.index));
    if (parsed !== null) frames.push(parsed);
    cursor = boundary.lastIndex;
  }
  return { frames, tail: source.slice(cursor) };
}

function parseSseFrames(source) {
  return consumeSseFrames(source).frames;
}

async function freePort() {
  const server = createNetServer();
  await new Promise((done, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", done);
  });
  const address = server.address();
  if (address === null || typeof address === "string") throw new Error("compatibility_port_failed");
  await new Promise((done) => server.close(done));
  return address.port;
}

function start(command, args, options) {
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: { ...process.env, ...options.env },
    detached: true,
    shell: false,
    stdio: "ignore",
  });
  children.add(child);
  child.once("exit", () => children.delete(child));
  child.once("error", () => children.delete(child));
  return child;
}

function childCompleted(child) {
  return child.exitCode !== null || child.signalCode !== null;
}

async function stopChild(child, options = {}) {
  const kill = options.kill ?? process.kill;
  const now = options.now ?? Date.now;
  const sleep = options.sleep ?? ((durationMs) => new Promise((done) => setTimeout(done, durationMs)));
  if (childCompleted(child) || child.pid === undefined) return;
  try { kill(-child.pid, "SIGTERM"); } catch {}
  const deadline = now() + 5_000;
  while (!childCompleted(child) && now() < deadline) {
    await sleep(50);
  }
  if (!childCompleted(child)) {
    try { kill(-child.pid, "SIGKILL"); } catch {}
  }
}

async function stopAll() {
  await Promise.allSettled([...children].map(stopChild));
}

function childExited(child) {
  return child !== undefined && (
    child.pid === undefined || childCompleted(child)
  );
}

function readinessReason(phase, kind, status = null) {
  if (!READINESS_PHASES.has(phase)) fail("readiness_phase_invalid");
  if (status === null) return `${phase}_readiness_${kind}`;
  const suffix = Number.isInteger(status) && status >= 100 && status <= 599
    ? String(status)
    : "unknown";
  if (kind === "rejected") return `${phase}_readiness_http_${suffix}`;
  return `${phase}_readiness_${kind}_http_${suffix}`;
}

async function waitHttp(url, options = {}) {
  const phase = options.phase;
  if (!READINESS_PHASES.has(phase)) fail("readiness_phase_invalid");
  const now = options.now ?? Date.now;
  const sleep = options.sleep ?? ((durationMs) => new Promise((done) => setTimeout(done, durationMs)));
  const fetchImpl = options.fetchImpl ?? fetch;
  const deadline = now() + (options.timeoutMs ?? 60_000);
  let lastStatus = null;
  while (now() < deadline) {
    if (childExited(options.child)) fail(readinessReason(phase, "child_exited"));
    try {
      const response = await fetchImpl(url, {
        signal: AbortSignal.timeout(2_000),
        ...(options.fetchOptions ?? {}),
      });
      lastStatus = response.status;
      if (options.accept?.includes(response.status) ?? response.status < 500) return response;
      try { await response.body?.cancel(); } catch {}
      if (response.status < 500) fail(readinessReason(phase, "rejected", response.status));
    } catch (error) {
      if (error instanceof ScenarioFailure) throw error;
    }
    if (childExited(options.child)) fail(readinessReason(phase, "child_exited"));
    await sleep(200);
  }
  if (childExited(options.child)) fail(readinessReason(phase, "child_exited"));
  fail(readinessReason(phase, "timeout", lastStatus));
}

function headerValue(request, name) {
  const value = request.headers[name];
  return typeof value === "string" ? value : null;
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "content-type": "application/json" });
  response.end(JSON.stringify(payload));
}

function sendFixtureError(response, statusCode, code) {
  sendJson(response, statusCode, { error: { code, message: "Compatibility fixture rejected request" } });
}

function hasExactQuery(url, key) {
  const entries = [...url.searchParams.entries()];
  return entries.length === 1 && entries[0][0] === key;
}

async function startBoundaryFixture({ siteHost = SITE_HOST } = {}) {
  const requests = [];
  const server = createHttpServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://compatibility.invalid");
    const caller = headerValue(request, "x-kokoro-service");
    const host = url.searchParams.get("host");
    const namespace = url.searchParams.get("namespace");
    requests.push({ method: request.method ?? null, pathname: url.pathname, caller, host, namespace });

    if (request.method !== "GET") {
      sendFixtureError(response, 405, "fixture.method_not_allowed");
      return;
    }
    if (url.pathname === "/site-context/resolve") {
      if (
        caller !== "web-bff" ||
        headerValue(request, "x-kokoro-internal-secret") !== WEB_INTERNAL_SECRET
      ) {
        sendFixtureError(response, 401, "fixture.unauthorized");
        return;
      }
      if (!hasExactQuery(url, "host")) {
        sendFixtureError(response, 400, "fixture.query_invalid");
        return;
      }
      if (host !== siteHost) {
        sendFixtureError(response, 404, "site_context.not_found");
        return;
      }
      const timestamp = "2026-01-01T00:00:00.000Z";
      sendJson(response, 200, {
        data: {
          context: {
            siteId: SITE_ID,
            siteKey: "compatibility",
            host: siteHost,
            defaultLocale: "en",
            timezone: "UTC",
            brand: { name: "Compatibility", logoUrl: null, themeColor: null },
          },
          site: {
            id: SITE_ID,
            key: "compatibility",
            name: "Compatibility",
            status: "active",
            defaultLocale: "en",
            timezone: "UTC",
            brandLogoUrl: null,
            brandThemeColor: null,
            createdAt: timestamp,
            updatedAt: timestamp,
            deletedAt: null,
            deletedBy: null,
            deleteReason: null,
          },
        },
      });
      return;
    }
    if (url.pathname === "/hub/runtime/resolve") {
      if (
        caller !== "session" ||
        headerValue(request, "x-kokoro-internal-secret") !== SESSION_INTERNAL_SECRET
      ) {
        sendFixtureError(response, 401, "fixture.unauthorized");
        return;
      }
      if (!hasExactQuery(url, "namespace")) {
        sendFixtureError(response, 400, "fixture.query_invalid");
        return;
      }
      if (namespace !== NAMESPACE) {
        sendFixtureError(response, 404, "hub_runtime.not_found");
        return;
      }
      sendJson(response, 200, { data: { skills: [], mcp_servers: [] } });
      return;
    }
    sendFixtureError(response, 404, "fixture.route_not_found");
  });
  await new Promise((done, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", done);
  });
  const address = server.address();
  if (address === null || typeof address === "string") fail("fixture_start_failed");
  return {
    server,
    requests,
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((done) => server.close(done)),
  };
}

async function requestWithAuthority(url, authority, headers = {}, options = {}) {
  if (
    typeof authority !== "string" ||
    authority.length === 0 ||
    authority.length > 253 ||
    /[\r\n/\\]/u.test(authority)
  ) {
    fail("site_probe_authority_invalid");
  }
  const timeoutMs = options.timeoutMs ?? 10_000;
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30_000) {
    fail("site_probe_timeout_invalid");
  }
  return new Promise((resolveRequest, rejectRequest) => {
    const request = httpRequest(url, {
      method: "GET",
      headers: { ...headers, host: authority },
      signal: AbortSignal.timeout(timeoutMs),
    }, (response) => {
      const chunks = [];
      let size = 0;
      response.on("data", (chunk) => {
        size += chunk.length;
        if (size > AUTHORITY_PROBE_MAX_BYTES) {
          response.destroy(new ScenarioFailure("site_probe_response_too_large"));
          return;
        }
        chunks.push(chunk);
      });
      response.once("error", rejectRequest);
      response.once("end", () => {
        let json;
        try {
          json = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        } catch {
          rejectRequest(new ScenarioFailure("site_probe_response_invalid"));
          return;
        }
        resolveRequest({ status: response.statusCode ?? 0, json });
      });
    });
    request.once("error", (error) => {
      if (error?.name === "AbortError") {
        rejectRequest(new ScenarioFailure("site_probe_timeout"));
        return;
      }
      rejectRequest(error);
    });
    request.end();
  });
}

async function readReplay(url, headers, options = {}) {
  const controller = new AbortController();
  const handshakeController = new AbortController();
  const handshakeTimeoutMs = options.handshakeTimeoutMs ?? 10_000;
  if (!Number.isInteger(handshakeTimeoutMs) || handshakeTimeoutMs < 1 || handshakeTimeoutMs > 30_000) {
    fail("sse_handshake_timeout_invalid");
  }
  const handshakeTimer = setTimeout(
    () => handshakeController.abort(new ScenarioFailure("sse_handshake_timeout")),
    handshakeTimeoutMs,
  );
  let response;
  try {
    response = await (options.fetchImpl ?? fetch)(url, {
      headers,
      signal: AbortSignal.any([controller.signal, handshakeController.signal]),
    });
  } catch {
    const handshakeTimedOut = handshakeController.signal.aborted;
    controller.abort();
    if (handshakeTimedOut) fail("sse_handshake_timeout");
    fail("sse_unreachable");
  } finally {
    clearTimeout(handshakeTimer);
  }
  if (response.status !== 200 || !response.headers.get("content-type")?.includes("text/event-stream")) {
    controller.abort();
    try { await response.body?.cancel(); } catch {}
    fail(`sse_http_${response.status}`);
  }
  const reader = response.body?.getReader();
  if (reader === undefined) fail("sse_body_missing");
  const decoder = new TextDecoder();
  let tail = "";
  const frames = [];
  const deadline = Date.now() + 15_000;
  try {
    while (Date.now() < deadline) {
      let timeout;
      const item = await Promise.race([
        reader.read(),
        new Promise((_, reject) => {
          timeout = setTimeout(() => reject(new ScenarioFailure("sse_read_timeout")), 2_000);
        }),
      ]).finally(() => clearTimeout(timeout));
      if (item.done) break;
      let consumed;
      try {
        consumed = consumeSseFrames(`${tail}${decoder.decode(item.value, { stream: true })}`);
      } catch {
        fail("sse_frame_invalid");
      }
      frames.push(...consumed.frames);
      tail = consumed.tail;
      if (frames.length >= 2) break;
    }
  } finally {
    controller.abort();
  }
  return frames.slice(0, 2);
}

function buildResult(outcome, reasonCode, durationMs) {
  return {
    schemaVersion: 1,
    scenarioId: "web-session-http-sse",
    outcome,
    reasonCode,
    assertionIds: [
      "web-session:bff-auth",
      "web-session:http-mutation",
      "web-session:sse-stream",
      "web-session:sse-resume",
      "web-session:site-binding",
      "web-session:namespace",
    ],
    durationMs,
  };
}

async function run() {
  const started = Date.now();
  let fixture;
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (!scopePath) fail("scope_missing");
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const [webPort, sessionPort] = await Promise.all([freePort(), freePort()]);
    fixture = await startBoundaryFixture();
    const webOrigin = `http://127.0.0.1:${webPort}`;
    const session = start("npm", ["run", "start"], {
      cwd: resolve(root, "kokoro-session"),
      env: buildSessionEnvironment(lease, { sessionPort, webOrigin, hubBaseUrl: fixture.baseUrl }),
    });
    await waitHttp(`http://127.0.0.1:${sessionPort}/sessions/compatibility-probe`, {
      phase: "session",
      child: session,
      accept: [401],
    });
    const web = start("pnpm", [
      "--filter", "@kokoro/web-user", "exec", "next", "dev",
      "--hostname", "127.0.0.1", "--port", String(webPort),
    ], {
      cwd: resolve(root, "kokoro-web"),
      env: buildWebEnvironment({
        sessionPort,
        userBaseUrl: fixture.baseUrl,
        siteBaseUrl: fixture.baseUrl,
      }),
    });
    await waitHttp(`${webOrigin}/api/session/sessions/compatibility-probe`, {
      phase: "web",
      child: web,
      accept: [401],
    });

    const now = Math.floor(Date.now() / 1000);
    const token = signToken(NAMESPACE, now + 3_600);
    const envelope = sealEnvelope({
      runtime_jwt: token,
      access_exp: now + 3_600,
      refresh_token: "compatibility-refresh-not-real",
      user_id: "user-compatibility",
      namespace: NAMESPACE,
      site_id: SITE_ID,
      exp: now + 7_200,
    });
    const cookie = `kokoro_session=${envelope}`;
    const namespaceContext = await fetch(`${webOrigin}/api/team/context`, {
      headers: { cookie },
      signal: AbortSignal.timeout(10_000),
    });
    if (
      namespaceContext.status !== 200 ||
      (await namespaceContext.json()).namespace !== NAMESPACE
    ) {
      fail("envelope_namespace_invalid");
    }

    const wrongSiteEnvelope = sealEnvelope({
      runtime_jwt: token,
      access_exp: now + 3_600,
      refresh_token: "compatibility-refresh-not-real",
      user_id: "user-compatibility",
      namespace: NAMESPACE,
      site_id: "site-other",
      exp: now + 7_200,
    });
    const wrongSite = await fetch(`${webOrigin}/api/session/sessions/compatibility-site-mismatch`, {
      headers: { cookie: `kokoro_session=${wrongSiteEnvelope}` },
      signal: AbortSignal.timeout(10_000),
    });
    if (wrongSite.status !== 401) fail(`site_binding_http_${wrongSite.status}`);

    const unknownHost = await requestWithAuthority(
      `${webOrigin}/api/session/sessions/compatibility-unknown-host`,
      "unbound.compatibility.invalid",
      { cookie },
    );
    if (
      unknownHost.status !== 404 ||
      unknownHost.json?.error !== "site_unresolved"
    ) {
      fail(`site_unresolved_http_${unknownHost.status}`);
    }

    const sessionId = `ses_compat_${randomBytes(5).toString("hex")}`;
    const accepted = await fetch(`${webOrigin}/api/session/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        cookie,
        origin: webOrigin,
        "content-type": "application/json",
      },
      body: JSON.stringify({ idempotency_key: `idem_${randomBytes(6).toString("hex")}`, content: "compatibility" }),
      signal: AbortSignal.timeout(15_000),
    });
    if (accepted.status !== 202) fail(`message_http_${accepted.status}`);
    const receipt = await accepted.json();
    if (typeof receipt.run_id !== "string" || receipt.run_id.length === 0) {
      fail("receipt_invalid");
    }
    const snapshot = await fetch(`${webOrigin}/api/session/sessions/${sessionId}`, {
      headers: { cookie },
      signal: AbortSignal.timeout(10_000),
    });
    if (snapshot.status !== 200 || (await snapshot.json()).session?.session_id !== sessionId) {
      fail(`snapshot_http_${snapshot.status}`);
    }
    const frames = await readReplay(
      `${webOrigin}/api/session/sessions/${sessionId}/events`,
      { cookie, accept: "text/event-stream", "last-event-id": "1" },
    );
    if (
      frames.length !== 2 ||
      frames[0].id !== 2 ||
      frames[0].event !== "run.created" ||
      frames[1].id !== 3 ||
      frames[1].event !== "message.user"
    ) {
      fail("sse_replay_invalid");
    }
    if (!fixture.requests.some(({ pathname, caller, namespace }) =>
      caller === "session" && pathname === "/hub/runtime/resolve" && namespace === NAMESPACE,
    )) {
      fail("session_namespace_not_forwarded");
    }
    if (!fixture.requests.some(({ pathname, caller, host }) =>
      caller === "web-bff" && pathname === "/site-context/resolve" && host === SITE_HOST,
    )) {
      fail("site_resolution_not_observed");
    }
    if (!fixture.requests.some(({ pathname, caller, host }) =>
      caller === "web-bff" &&
      pathname === "/site-context/resolve" &&
      host === "unbound.compatibility.invalid",
    )) {
      fail("site_unresolved_not_observed");
    }
    await stopChild(web);
    await stopChild(session);
    return buildResult("pass", "ok", Date.now() - started);
  } catch (error) {
    return buildResult(
      "fail",
      error instanceof ScenarioFailure ? error.reasonCode : "web_session_live_failed",
      Date.now() - started,
    );
  } finally {
    await stopAll();
    if (fixture !== undefined) await fixture.close();
  }
}

async function main() {
  const machine = await run();
  writeSync(3, `${JSON.stringify(machine)}\n`);
  process.exitCode = machine.outcome === "pass" ? 0 : 1;
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  const terminate = () => { void stopAll().finally(() => process.exit(143)); };
  process.once("SIGINT", terminate);
  process.once("SIGTERM", terminate);
  await main();
}

export {
  buildResult,
  buildSessionEnvironment,
  buildWebEnvironment,
  consumeSseFrames,
  parseSseFrames,
  sealEnvelope,
  signToken,
  startBoundaryFixture,
  stopChild,
  waitHttp,
  readReplay,
  requestWithAuthority,
};
