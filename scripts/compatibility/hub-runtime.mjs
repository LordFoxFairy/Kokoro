#!/usr/bin/env node

import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { writeSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer as createNetServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { startMembershipFixture } from "./hub-runtime-membership-fixture.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const REQUIRED_RESOURCES = ["mongo", "redis"];
const SAFE_PARENT_ENV_KEYS = ["PATH", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP"];
const MAX_DURATION_MS = 179_999;
const MAX_PROBE_OUTPUT_BYTES = 16 * 1024;
const children = new Set();
const processErrors = new WeakMap();

const SESSION_SECRET = "compatibility-session-not-real";
const AGENT_SECRET = "compatibility-agent-not-real";
const WEB_BFF_SECRET = "compatibility-web-bff-not-real";
const ADMIN_SECRET = "compatibility-admin-not-real";
const HUB_SECRET = "compatibility-hub-not-real";
const MASTER_KEY = Buffer.alloc(32, 7).toString("base64");
const NAMESPACE = "namespace-hub-compatibility";
const USER_ID = "user-hub-compatibility";
const SECRET_VALUE = "compatibility-secret-value-not-real";

export const HUB_START_COMMAND = ["pnpm", "--filter", "@kokoro/hub", "run", "start"];
export const SESSION_PROBE_COMMAND = ["npm", "run", "--silent", "compat:hub-runtime", "--"];
export const AGENT_PROBE_COMMAND = [
  "uv", "run", "--locked", "python", "scripts/compat/hub_runtime_consumer.py",
];
export const ASSERTION_IDS = [
  "hub-runtime:membership-authorizer",
  "hub-runtime:self-secret-create",
  "hub-runtime:session-capability-resolve",
  "hub-runtime:agent-secret-resolve",
  "hub-runtime:missing-caller-rejected",
  "hub-runtime:wrong-caller-rejected",
  "hub-runtime:cross-namespace-secret-rejected",
  "hub-runtime:process-cleanup",
];

export function validateLease(value) {
  const runId = value?.runId;
  const databaseStem = typeof runId === "string"
    ? `kokoro_test_${runId}`.replaceAll("-", "_")
    : "";
  if (
    value === null ||
    typeof value !== "object" ||
    value.schemaVersion !== 1 ||
    !/^run_[a-z0-9][a-z0-9_-]{2,31}$/u.test(runId ?? "") ||
    !Array.isArray(value.resources) ||
    new Set(value.resources).size !== value.resources.length ||
    REQUIRED_RESOURCES.some((resource) => !value.resources.includes(resource)) ||
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

export function buildHubEnvironment(
  lease,
  { hubPort, membershipBaseUrl, parentEnv = process.env },
) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    KOKORO_HUB_PORT: String(hubPort),
    KOKORO_HUB_MONGO_URL: "mongodb://127.0.0.1:27017",
    KOKORO_HUB_MONGO_DB: lease.mongo.database,
    KOKORO_USER_BASE_URL: membershipBaseUrl,
    KOKORO_HUB_SECRET_MASTER_KEY: MASTER_KEY,
    KOKORO_HUB_MCP_MUTATION: "on",
    KOKORO_INTERNAL_SECRET_SESSION: SESSION_SECRET,
    KOKORO_INTERNAL_SECRET_AGENT: AGENT_SECRET,
    KOKORO_INTERNAL_SECRET_WEB_BFF: WEB_BFF_SECRET,
    KOKORO_INTERNAL_SECRET_ADMIN: ADMIN_SECRET,
    KOKORO_INTERNAL_SECRET_HUB: HUB_SECRET,
  });
}

export function buildResult(passed, durationMs) {
  const finiteDuration = Number.isFinite(durationMs) ? Math.trunc(durationMs) : 0;
  return {
    schemaVersion: 1,
    scenarioId: "hub-runtime",
    outcome: passed ? "pass" : "fail",
    reasonCode: passed ? "ok" : "hub_runtime_live_failed",
    assertionIds: ASSERTION_IDS,
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
  if (address === null || typeof address === "string") throw new Error("compatibility_port_failed");
  await new Promise((done) => server.close(done));
  return address.port;
}

function start(command, { cwd, env, capture = false }) {
  const [executable, ...args] = command;
  const child = spawn(executable, args, {
    cwd,
    env,
    detached: true,
    shell: false,
    stdio: capture ? ["ignore", "pipe", "ignore"] : "ignore",
  });
  children.add(child);
  child.once("error", (error) => {
    processErrors.set(child, error);
    children.delete(child);
  });
  child.once("exit", () => children.delete(child));
  return child;
}

function childExited(child) {
  return processErrors.has(child) || child.exitCode !== null || child.signalCode !== null;
}

async function stopChild(child) {
  if (childExited(child) || child.pid === undefined) return true;
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch (error) {
    if (error.code !== "ESRCH") return false;
  }
  const deadline = Date.now() + 5_000;
  while (!childExited(child) && Date.now() < deadline) {
    await new Promise((done) => setTimeout(done, 50));
  }
  if (!childExited(child)) {
    try {
      process.kill(-child.pid, "SIGKILL");
    } catch (error) {
      if (error.code !== "ESRCH") return false;
    }
  }
  const killDeadline = Date.now() + 2_000;
  while (!childExited(child) && Date.now() < killDeadline) {
    await new Promise((done) => setTimeout(done, 25));
  }
  return childExited(child);
}

async function stopAll() {
  const active = [...children];
  const results = await Promise.all(active.map(stopChild));
  return results.every(Boolean);
}

async function waitHttp(url, child, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (childExited(child)) throw new Error("compatibility_service_exited");
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.status < 500) return response;
    } catch {}
    await new Promise((done) => setTimeout(done, 200));
  }
  throw new Error("compatibility_service_not_ready");
}

async function runProbe(command, { cwd, env, timeoutMs = 45_000 }) {
  const child = start(command, { cwd, env, capture: true });
  const chunks = [];
  let bytes = 0;
  child.stdout?.on("data", (chunk) => {
    bytes += chunk.byteLength;
    if (bytes <= MAX_PROBE_OUTPUT_BYTES) chunks.push(chunk);
  });
  const exitCode = await new Promise((done, reject) => {
    if (processErrors.has(child)) {
      reject(new Error("compatibility_probe_spawn_failed"));
      return;
    }
    const timer = setTimeout(() => {
      void stopChild(child);
      reject(new Error("compatibility_probe_timeout"));
    }, timeoutMs);
    child.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.once("exit", (code) => {
      clearTimeout(timer);
      done(code);
    });
  });
  if (exitCode !== 0 || bytes > MAX_PROBE_OUTPUT_BYTES) throw new Error("compatibility_probe_failed");
  const lines = Buffer.concat(chunks).toString("utf8").split(/\r?\n/u).filter(Boolean);
  if (lines.length !== 1) throw new Error("compatibility_probe_protocol");
  return JSON.parse(lines[0]);
}

function selfHeaders() {
  return {
    "content-type": "application/json",
    "x-kokoro-service": "web-bff",
    "x-kokoro-internal-secret": WEB_BFF_SECRET,
    "x-kokoro-namespace": NAMESPACE,
    "x-kokoro-user-id": USER_ID,
  };
}

function runtimeHeaders(caller, secret) {
  return {
    "content-type": "application/json",
    "x-kokoro-service": caller,
    "x-kokoro-internal-secret": secret,
  };
}

async function run() {
  const started = Date.now();
  let passed = false;
  let membership = null;
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (typeof scopePath !== "string" || scopePath.length === 0) throw new Error("compatibility_scope_missing");
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const hubPort = await freePort();
    membership = await startMembershipFixture({
      port: 0,
      internalSecret: HUB_SECRET,
      namespace: NAMESPACE,
      userId: USER_ID,
    });
    const hubBaseUrl = `http://127.0.0.1:${hubPort}`;
    const hubEnv = buildHubEnvironment(lease, {
      hubPort,
      membershipBaseUrl: membership.baseUrl,
    });
    const hub = start(HUB_START_COMMAND, {
      cwd: resolve(root, "kokoro-platform"),
      env: hubEnv,
    });
    await waitHttp(`${hubBaseUrl}/healthz`, hub);

    const missing = await fetch(`${hubBaseUrl}/hub/runtime/resolve?namespace=${NAMESPACE}`);
    if (missing.status !== 401) throw new Error("compatibility_missing_caller_not_rejected");
    const wrong = await fetch(`${hubBaseUrl}/hub/runtime/resolve?namespace=${NAMESPACE}`, {
      headers: runtimeHeaders("web-bff", WEB_BFF_SECRET),
    });
    if (wrong.status !== 403) throw new Error("compatibility_wrong_caller_not_rejected");

    const created = await fetch(`${hubBaseUrl}/hub/self/mcp/secrets`, {
      method: "POST",
      headers: selfHeaders(),
      body: JSON.stringify({ name: "compatibility-secret", value: SECRET_VALUE }),
      signal: AbortSignal.timeout(10_000),
    });
    if (created.status !== 201) throw new Error("compatibility_secret_create_failed");
    const createdBody = await created.json();
    const handle = createdBody?.data?.handle;
    if (!/^srt_[0-9a-f]{32}$/u.test(handle ?? "")) throw new Error("compatibility_secret_handle_invalid");

    const sessionResult = await runProbe([
      ...SESSION_PROBE_COMMAND,
      "--base-url", hubBaseUrl,
      "--namespace", NAMESPACE,
    ], {
      cwd: resolve(root, "kokoro-session"),
      env: isolatedEnvironment(process.env, { KOKORO_INTERNAL_SECRET_SESSION: SESSION_SECRET }),
    });
    if (
      sessionResult?.schemaVersion !== 1 ||
      !Number.isInteger(sessionResult.skills) ||
      !Number.isInteger(sessionResult.mcpServers)
    ) throw new Error("compatibility_session_probe_invalid");

    const expectedDigest = createHash("sha256").update(SECRET_VALUE).digest("hex");
    const agentResult = await runProbe([
      ...AGENT_PROBE_COMMAND,
      "--base-url", hubBaseUrl,
      "--namespace", NAMESPACE,
      "--handle", handle,
      "--expected-sha256", expectedDigest,
    ], {
      cwd: resolve(root, "kokoro-agent"),
      env: isolatedEnvironment(process.env, { KOKORO_INTERNAL_SECRET_AGENT: AGENT_SECRET }),
    });
    if (agentResult?.schemaVersion !== 1 || agentResult.resolvedHandles !== 1) {
      throw new Error("compatibility_agent_probe_invalid");
    }

    const crossNamespace = await fetch(`${hubBaseUrl}/hub/runtime/mcp/secrets/resolve`, {
      method: "POST",
      headers: runtimeHeaders("agent", AGENT_SECRET),
      body: JSON.stringify({ namespace: "namespace-other", handles: [handle] }),
      signal: AbortSignal.timeout(10_000),
    });
    if (crossNamespace.status !== 404) throw new Error("compatibility_cross_namespace_not_rejected");
    passed = true;
  } catch {
    passed = false;
  }
  const cleanup = await stopAll();
  if (membership !== null) {
    try {
      await membership.close();
    } catch {
      passed = false;
    }
  }
  return buildResult(passed && cleanup, Date.now() - started);
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
