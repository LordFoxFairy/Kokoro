#!/usr/bin/env node

import { createCipheriv, createHash, createHmac, randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { writeSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer as createHttpServer } from "node:http";
import { createServer as createNetServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const AUTH_SECRET = "compatibility-hs256-not-real";
const WEB_SECRET = "compatibility-envelope-not-real";
const SITE_ID = "site-compatibility";
const NAMESPACE = "namespace-compatibility";
const children = new Set();

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
    KOKORO_INTERNAL_SECRET_SESSION: "compatibility-session-not-real",
    KOKORO_BILLING_MODE: "off",
    KOKORO_WORKSPACE_ROOT: resolve(root, "tmp/compatibility-workspaces", lease.runId),
  };
}

function buildWebEnvironment({ sessionPort, userBaseUrl }) {
  return {
    KOKORO_WEB_SESSION_SECRET: WEB_SECRET,
    KOKORO_USER_BASE_URL: userBaseUrl,
    KOKORO_SESSION_BASE_URL: `http://127.0.0.1:${sessionPort}`,
    KOKORO_SITE_ID: SITE_ID,
    KOKORO_INTERNAL_SECRET_WEB_BFF: "compatibility-web-not-real",
  };
}

function parseSseFrames(source) {
  return source.split("\n\n").filter(Boolean).map((block) => {
    const fields = new Map();
    for (const line of block.split("\n")) {
      const separator = line.indexOf(": ");
      if (separator > 0) fields.set(line.slice(0, separator), line.slice(separator + 2));
    }
    return {
      id: Number(fields.get("id")),
      event: fields.get("event"),
      data: JSON.parse(fields.get("data")),
    };
  });
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
  return child;
}

async function stopChild(child) {
  if (child.exitCode !== null || child.pid === undefined) return;
  try { process.kill(-child.pid, "SIGTERM"); } catch {}
  const deadline = Date.now() + 5_000;
  while (child.exitCode === null && Date.now() < deadline) {
    await new Promise((done) => setTimeout(done, 50));
  }
  if (child.exitCode === null) {
    try { process.kill(-child.pid, "SIGKILL"); } catch {}
  }
}

async function stopAll() {
  await Promise.allSettled([...children].map(stopChild));
}

async function waitHttp(url, options = {}) {
  const deadline = Date.now() + (options.timeoutMs ?? 60_000);
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000), ...(options.fetch ?? {}) });
      if (options.accept?.includes(response.status) ?? response.status < 500) return response;
    } catch {}
    await new Promise((done) => setTimeout(done, 200));
  }
  throw new Error("compatibility_service_not_ready");
}

async function startHubFixture() {
  const requests = [];
  const server = createHttpServer((request, response) => {
    requests.push({ url: request.url, caller: request.headers["x-kokoro-service"] });
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ data: { skills: [], mcp_servers: [] } }));
  });
  await new Promise((done, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", done);
  });
  const address = server.address();
  if (address === null || typeof address === "string") throw new Error("compatibility_hub_failed");
  return { server, requests, baseUrl: `http://127.0.0.1:${address.port}` };
}

async function readReplay(url, headers) {
  const controller = new AbortController();
  const response = await fetch(url, { headers, signal: controller.signal });
  if (response.status !== 200 || !response.headers.get("content-type")?.includes("text/event-stream")) {
    controller.abort();
    throw new Error("compatibility_sse_status");
  }
  const reader = response.body?.getReader();
  if (reader === undefined) throw new Error("compatibility_sse_body");
  const decoder = new TextDecoder();
  let buffer = "";
  const deadline = Date.now() + 15_000;
  try {
    while (Date.now() < deadline) {
      const item = await Promise.race([
        reader.read(),
        new Promise((_, reject) => setTimeout(() => reject(new Error("compatibility_sse_timeout")), 2_000)),
      ]);
      if (item.done) break;
      buffer += decoder.decode(item.value, { stream: true });
      if (parseSseFrames(buffer).length >= 2) break;
    }
  } finally {
    controller.abort();
  }
  return parseSseFrames(buffer).slice(0, 2);
}

function result(outcome, reasonCode, durationMs) {
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
      "web-session:namespace",
    ],
    durationMs,
  };
}

async function run() {
  const started = Date.now();
  let hub;
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (!scopePath) throw new Error("compatibility_scope_missing");
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const [webPort, sessionPort] = await Promise.all([freePort(), freePort()]);
    hub = await startHubFixture();
    const webOrigin = `http://127.0.0.1:${webPort}`;
    const session = start("npm", ["run", "start"], {
      cwd: resolve(root, "kokoro-session"),
      env: buildSessionEnvironment(lease, { sessionPort, webOrigin, hubBaseUrl: hub.baseUrl }),
    });
    await waitHttp(`http://127.0.0.1:${sessionPort}/sessions/compatibility-probe`, { accept: [401, 404] });
    const web = start("pnpm", [
      "--filter", "@kokoro/web-user", "exec", "next", "dev",
      "--hostname", "127.0.0.1", "--port", String(webPort),
    ], {
      cwd: resolve(root, "kokoro-web"),
      env: buildWebEnvironment({ sessionPort, userBaseUrl: hub.baseUrl }),
    });
    await waitHttp(`${webOrigin}/api/session/sessions/compatibility-probe`, { accept: [401] });

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
    if (accepted.status !== 202) throw new Error("compatibility_message_not_accepted");
    const receipt = await accepted.json();
    if (typeof receipt.run_id !== "string" || receipt.run_id.length === 0) {
      throw new Error("compatibility_receipt_invalid");
    }
    const snapshot = await fetch(`${webOrigin}/api/session/sessions/${sessionId}`, {
      headers: { cookie },
      signal: AbortSignal.timeout(10_000),
    });
    if (snapshot.status !== 200 || (await snapshot.json()).session?.session_id !== sessionId) {
      throw new Error("compatibility_snapshot_invalid");
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
      throw new Error("compatibility_sse_replay_invalid");
    }
    if (!hub.requests.some(({ url, caller }) =>
      caller === "session" && url === `/hub/runtime/resolve?namespace=${NAMESPACE}`,
    )) {
      throw new Error("compatibility_namespace_not_forwarded");
    }
    await stopChild(web);
    await stopChild(session);
    return result("pass", "ok", Date.now() - started);
  } catch {
    return result("fail", "web_session_live_failed", Date.now() - started);
  } finally {
    if (hub !== undefined) await new Promise((done) => hub.server.close(done));
    await stopAll();
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
  buildSessionEnvironment,
  buildWebEnvironment,
  parseSseFrames,
  sealEnvelope,
  signToken,
};
