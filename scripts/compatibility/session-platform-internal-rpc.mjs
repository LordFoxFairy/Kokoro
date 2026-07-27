#!/usr/bin/env node

import { createHmac } from "node:crypto";
import { spawn } from "node:child_process";
import { writeSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer as createNetServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const MYSQL_CONTEXTS = ["site", "user", "model", "credit", "payment", "admin"];
const REQUIRED_RESOURCES = ["mysql", "mongo", "redis"];
const SAFE_PARENT_ENV_KEYS = ["PATH", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP"];
const children = new Set();
const processErrors = new WeakMap();

const AUTH_SECRET = "compatibility-hs256-not-real";
const INTERNAL_SECRET = "compatibility-session-not-real";
const SITE_ID = "site-compatibility";
const NAMESPACE = "namespace-compatibility";
const MAX_DURATION_MS = 179_999;
const ASSERTION_IDS = [
  "session-platform:session-model-catalog",
  "session-platform:platform-binding-resolve",
  "session-platform:missing-caller-rejected",
  "session-platform:wrong-caller-rejected",
  "session-platform:session-caller-authorized",
];

function validateLease(value) {
  const runId = value?.runId;
  const databaseStem = typeof runId === "string"
    ? `kokoro_test_${runId}`.replaceAll("-", "_")
    : "";
  const resources = value?.resources;
  const mysqlShapeValid = MYSQL_CONTEXTS.every((context) =>
    value?.mysql?.[context] === `${databaseStem}_${context}` &&
    /^kt_[a-z0-9_]+$/u.test(value?.mysqlUsers?.[context]?.username ?? "") &&
    typeof value?.mysqlUsers?.[context]?.password === "string" &&
    value.mysqlUsers[context].password.length >= 2,
  );
  if (
    value === null ||
    typeof value !== "object" ||
    value.schemaVersion !== 1 ||
    !/^run_[a-z0-9][a-z0-9_-]{2,31}$/u.test(runId ?? "") ||
    !/^[a-z0-9][a-z0-9._-]{1,63}$/u.test(value.endpointFingerprint ?? "") ||
    !Array.isArray(resources) ||
    new Set(resources).size !== resources.length ||
    REQUIRED_RESOURCES.some((resource) => !resources.includes(resource)) ||
    !mysqlShapeValid ||
    value.mongo?.database !== databaseStem ||
    !Number.isInteger(value.redis?.database) ||
    value.redis.database < 8 ||
    value.redis.database > 15 ||
    value.redis.keyPrefix !== `${databaseStem}:` ||
    value.redis.markerKey !== `${databaseStem}:__lease` ||
    value.redis.exclusive !== true
  ) {
    throw new Error("compatibility_scope_invalid");
  }
  return value;
}

function isolatedEnvironment(parentEnv, explicit) {
  const environment = {};
  for (const key of SAFE_PARENT_ENV_KEYS) {
    const value = parentEnv[key];
    if (typeof value === "string" && value.length > 0) environment[key] = value;
  }
  return { ...environment, ...explicit };
}

function modelDatabaseUrl(lease) {
  const url = new URL("mysql://127.0.0.1:3307");
  url.username = lease.mysqlUsers.model.username;
  url.password = lease.mysqlUsers.model.password;
  url.pathname = `/${lease.mysql.model}`;
  return url.href;
}

function buildModelEnvironment(lease, { modelPort, parentEnv = process.env }) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    DATABASE_URL_MODEL: modelDatabaseUrl(lease),
    KOKORO_MODEL_PORT: String(modelPort),
    KOKORO_INTERNAL_SECRET_SESSION: INTERNAL_SECRET,
  });
}

function buildSessionEnvironment(
  lease,
  { sessionPort, modelBaseUrl, parentEnv = process.env },
) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    KOKORO_SESSION_PORT: String(sessionPort),
    KOKORO_REDIS_URL: `redis://127.0.0.1:6379/${lease.redis.database}`,
    KOKORO_MESSAGE_STORE_MONGO_URL: "mongodb://127.0.0.1:27017",
    KOKORO_MESSAGE_STORE_MONGO_DB: lease.mongo.database,
    KOKORO_WEB_ORIGIN: "http://127.0.0.1",
    KOKORO_AUTH_MODE: "hs256",
    KOKORO_AUTH_JWT_SECRET: AUTH_SECRET,
    KOKORO_BILLING_MODE: "shadow",
    KOKORO_MODEL_BASE_URL: modelBaseUrl,
    KOKORO_CREDIT_BASE_URL: modelBaseUrl,
    KOKORO_HUB_BASE_URL: modelBaseUrl,
    KOKORO_SITE_ID: SITE_ID,
    KOKORO_BILLING_FEATURE_KEY: "chat",
    KOKORO_INTERNAL_SECRET_SESSION: INTERNAL_SECRET,
    KOKORO_WORKSPACE_ROOT: resolve(root, "tmp/compatibility-workspaces", lease.runId),
  });
}

function encodeJson(value) {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function signToken(subject, expiresAt) {
  const head = encodeJson({ alg: "HS256", typ: "JWT" });
  const body = encodeJson({ sub: subject, exp: expiresAt });
  const signature = createHmac("sha256", AUTH_SECRET)
    .update(`${head}.${body}`)
    .digest("base64url");
  return `${head}.${body}.${signature}`;
}

function platformRequestHeaders(internalSecret = INTERNAL_SECRET) {
  return {
    "x-kokoro-service": "session",
    "x-kokoro-internal-secret": internalSecret,
    "x-kokoro-site-id": SITE_ID,
  };
}

function buildResult(passed, durationMs) {
  const finiteDuration = Number.isFinite(durationMs) ? Math.trunc(durationMs) : 0;
  return {
    schemaVersion: 1,
    scenarioId: "session-platform-internal-rpc",
    outcome: passed ? "pass" : "fail",
    reasonCode: passed ? "ok" : "session_platform_live_failed",
    assertionIds: [...ASSERTION_IDS],
    durationMs: Math.min(MAX_DURATION_MS, Math.max(0, finiteDuration)),
  };
}

async function freePort() {
  const server = createNetServer();
  await new Promise((done, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", done);
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("compatibility_port_failed");
  }
  await new Promise((done) => server.close(done));
  return address.port;
}

function start(command, args, { cwd, env }) {
  const child = spawn(command, args, {
    cwd,
    env,
    detached: true,
    shell: false,
    stdio: "ignore",
  });
  children.add(child);
  child.once("error", (error) => {
    processErrors.set(child, error);
    children.delete(child);
  });
  child.once("exit", () => children.delete(child));
  return child;
}

async function stopChild(child) {
  if (child.exitCode !== null || child.pid === undefined) return;
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch {}
  const deadline = Date.now() + 5_000;
  while (child.exitCode === null && Date.now() < deadline) {
    await new Promise((done) => setTimeout(done, 50));
  }
  if (child.exitCode === null) {
    try {
      process.kill(-child.pid, "SIGKILL");
    } catch {}
  }
}

async function stopAll() {
  await Promise.allSettled([...children].map(stopChild));
}

async function waitForExit(child, timeoutMs) {
  if (processErrors.has(child)) throw new Error("compatibility_command_spawn_failed");
  if (child.exitCode !== null) {
    if (child.exitCode !== 0) throw new Error("compatibility_command_failed");
    return;
  }
  await new Promise((done, reject) => {
    const timer = setTimeout(() => {
      void stopChild(child);
      reject(new Error("compatibility_command_timeout"));
    }, timeoutMs);
    child.once("error", () => {
      clearTimeout(timer);
      reject(new Error("compatibility_command_spawn_failed"));
    });
    child.once("exit", (code) => {
      clearTimeout(timer);
      if (code === 0) done();
      else reject(new Error("compatibility_command_failed"));
    });
  });
}

async function runOfficialCommand(args, env) {
  const child = start("pnpm", args, { cwd: resolve(root, "kokoro-platform"), env });
  await waitForExit(child, 45_000);
}

async function waitHttp(url, { child, timeoutMs = 30_000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child?.exitCode !== null) throw new Error("compatibility_service_exited");
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.status < 500) return response;
    } catch {}
    await new Promise((done) => setTimeout(done, 200));
  }
  throw new Error("compatibility_service_not_ready");
}

async function request(url, options = {}) {
  return fetch(url, { ...options, signal: AbortSignal.timeout(10_000) });
}

function assertResolvedBinding(payload) {
  const binding = Array.isArray(payload?.data) ? payload.data[0] : undefined;
  if (
    binding?.transportKind !== "litellm" ||
    binding.gatewayModelName !== "claude-code"
  ) {
    throw new Error("compatibility_platform_binding_invalid");
  }
}

function assertSessionCatalog(payload) {
  const models = payload?.models;
  if (
    !Array.isArray(models) ||
    !models.some((model) =>
      model?.name === "claude-code" &&
      model.display_name === "Kokoro 默认" &&
      model.provider === "litellm",
    )
  ) {
    throw new Error("compatibility_session_catalog_invalid");
  }
}

async function run() {
  const started = Date.now();
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (typeof scopePath !== "string" || scopePath.length === 0) {
      throw new Error("compatibility_scope_missing");
    }
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const [modelPort, sessionPort] = await Promise.all([freePort(), freePort()]);
    const modelBaseUrl = `http://127.0.0.1:${modelPort}`;
    const modelEnv = buildModelEnvironment(lease, { modelPort });
    const sessionEnv = buildSessionEnvironment(lease, { sessionPort, modelBaseUrl });

    await runOfficialCommand(["--filter", "@kokoro/model", "run", "db:migrate"], modelEnv);
    await runOfficialCommand(["--filter", "@kokoro/model", "run", "seed:builtin"], modelEnv);

    const model = start(
      "pnpm",
      ["--filter", "@kokoro/model", "run", "start"],
      { cwd: resolve(root, "kokoro-platform"), env: modelEnv },
    );
    await waitHttp(`${modelBaseUrl}/healthz`, { child: model });

    const resolveUrl = new URL("/model-bindings/resolve", modelBaseUrl);
    // siteId is a required query parameter: model applies that Site's hidden-label policy
    // from it. Omitting it now fails schema validation before the caller checks below run,
    // which would silently stop this scenario from testing authorization at all.
    resolveUrl.search = new URLSearchParams({
      siteId: SITE_ID,
      featureKey: "chat",
      labelKey: "claude-code",
    });
    const missing = await request(resolveUrl, { headers: { "x-kokoro-site-id": SITE_ID } });
    if (missing.status !== 401) throw new Error("compatibility_missing_caller_not_rejected");
    const wrong = await request(resolveUrl, { headers: platformRequestHeaders("wrong-not-real") });
    if (wrong.status !== 401) throw new Error("compatibility_wrong_caller_not_rejected");
    const authorized = await request(resolveUrl, { headers: platformRequestHeaders() });
    if (authorized.status !== 200) throw new Error("compatibility_session_caller_rejected");
    assertResolvedBinding(await authorized.json());

    const sessionBaseUrl = `http://127.0.0.1:${sessionPort}`;
    const session = start(
      "npm",
      ["run", "start"],
      { cwd: resolve(root, "kokoro-session"), env: sessionEnv },
    );
    await waitHttp(`${sessionBaseUrl}/healthz`, { child: session });
    const expiresAt = Math.floor(Date.now() / 1_000) + 3_600;
    const catalog = await request(`${sessionBaseUrl}/models`, {
      headers: { authorization: `Bearer ${signToken(NAMESPACE, expiresAt)}` },
    });
    if (catalog.status !== 200) throw new Error("compatibility_session_models_rejected");
    assertSessionCatalog(await catalog.json());

    return buildResult(true, Date.now() - started);
  } catch {
    return buildResult(false, Date.now() - started);
  } finally {
    await stopAll();
  }
}

async function main() {
  const machine = await run();
  try {
    writeSync(3, `${JSON.stringify(machine)}\n`);
  } catch {
    process.exitCode = 1;
    return;
  }
  process.exitCode = machine.outcome === "pass" ? 0 : 1;
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  const terminate = () => {
    void stopAll().finally(() => process.exit(143));
  };
  process.once("SIGINT", terminate);
  process.once("SIGTERM", terminate);
  await main();
}

export {
  AUTH_SECRET,
  INTERNAL_SECRET,
  buildModelEnvironment,
  buildResult,
  buildSessionEnvironment,
  platformRequestHeaders,
  signToken,
  validateLease,
};
