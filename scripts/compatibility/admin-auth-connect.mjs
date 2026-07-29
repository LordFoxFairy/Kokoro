#!/usr/bin/env node

import { spawn } from "node:child_process";
import { writeSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer as createNetServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { contractMetadata } from "../../contract/generate.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const MYSQL_CONTEXTS = ["site", "user", "model", "credit", "payment", "admin"];
const SAFE_PARENT_ENV_KEYS = ["PATH", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP"];
const MAX_DURATION_MS = 179_999;
const children = new Set();
const processErrors = new WeakMap();

const CONTRACT_DIGEST = (await contractMetadata()).artifactDigestSha256;
const WORKLOAD_SECRET = "compatibility-admin-web-not-real";
const PLATFORM_MIGRATE_COMMAND = ["pnpm", "--filter", "@kokoro/platform-admin", "run", "db:migrate"];
const PLATFORM_SEED_COMMAND = ["pnpm", "--filter", "@kokoro/platform-admin", "run", "db:seed"];
const PLATFORM_START_COMMAND = ["pnpm", "--filter", "@kokoro/platform-admin", "run", "start"];
const WEB_PROBE_COMMAND = ["pnpm", "--filter", "@kokoro/admin-web", "run", "compat:admin-auth"];
const ASSERTION_IDS = [
  "admin-auth:generated-digest",
  "admin-auth:operator-lookup",
  "admin-auth:missing-credential-rejected",
  "admin-auth:wrong-audience-rejected",
  "admin-auth:invalid-request-rejected",
  "admin-auth:contract-skew-rejected",
  "admin-auth:duplicate-consume-idempotent",
  "admin-auth:digest-mismatch-rejected",
  "admin-auth:payload-digest-verified",
  "admin-auth:receipt-reconcile",
  "admin-auth:process-cleanup",
];

function validateLease(value) {
  const runId = value?.runId;
  const databaseStem = typeof runId === "string" ? `kokoro_test_${runId}`.replaceAll("-", "_") : "";
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
    !Array.isArray(resources) ||
    new Set(resources).size !== resources.length ||
    !resources.includes("mysql") ||
    !mysqlShapeValid
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

function adminDatabaseUrl(lease) {
  const url = new URL("mysql://127.0.0.1:3307");
  url.username = lease.mysqlUsers.admin.username;
  url.password = lease.mysqlUsers.admin.password;
  url.pathname = `/${lease.mysql.admin}`;
  return url.href;
}

function buildPlatformEnvironment(lease, { port, parentEnv = process.env }) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    DATABASE_URL_ADMIN: adminDatabaseUrl(lease),
    KOKORO_ADMIN_PORT: String(port),
    KOKORO_ADMIN_AUTH_MODE: "proxy",
    KOKORO_ADMIN_PROXY_SECRETS: WORKLOAD_SECRET,
    KOKORO_INTERNAL_SECRET_ADMIN: WORKLOAD_SECRET,
    KOKORO_ADMIN_AUTH_CONTRACT_DIGEST: CONTRACT_DIGEST,
  });
}

function buildWebEnvironment({ platformPort, parentEnv = process.env }) {
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    KOKORO_GATEWAY_URL: `http://127.0.0.1:${platformPort}`,
    KOKORO_ADMIN_PROXY_SECRET: WORKLOAD_SECRET,
    KOKORO_ADMIN_AUTH_CONTRACT_DIGEST: CONTRACT_DIGEST,
  });
}

function buildResult(passed, durationMs) {
  const finiteDuration = Number.isFinite(durationMs) ? Math.trunc(durationMs) : 0;
  return {
    schemaVersion: 1,
    scenarioId: "platform-admin-auth-connect",
    outcome: passed ? "pass" : "fail",
    reasonCode: passed ? "ok" : "platform_admin_auth_live_failed",
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
  if (address === null || typeof address === "string") throw new Error("compatibility_port_failed");
  await new Promise((done) => server.close(done));
  return address.port;
}

function start(command, { cwd, env }) {
  const [executable, ...args] = command;
  const child = spawn(executable, args, {
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

function childExited(child) {
  return child.exitCode !== null || child.signalCode !== null;
}

async function stopChild(child) {
  if (childExited(child) || child.pid === undefined) return;
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch {}
  const deadline = Date.now() + 5_000;
  while (!childExited(child) && Date.now() < deadline) {
    await new Promise((done) => setTimeout(done, 50));
  }
  if (!childExited(child)) {
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
  if (childExited(child)) {
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

async function runCommand(command, options, timeoutMs = 60_000) {
  const child = start(command, options);
  await waitForExit(child, timeoutMs);
}

async function waitHttp(url, { child, timeoutMs = 30_000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child !== undefined && childExited(child)) throw new Error("compatibility_service_exited");
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.status < 500) return;
    } catch {}
    await new Promise((done) => setTimeout(done, 200));
  }
  throw new Error("compatibility_service_not_ready");
}

async function run() {
  const started = Date.now();
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (typeof scopePath !== "string" || scopePath.length === 0) throw new Error("compatibility_scope_missing");
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const port = await freePort();
    const platformEnv = buildPlatformEnvironment(lease, { port });
    const webEnv = buildWebEnvironment({ platformPort: port });
    const platformRoot = resolve(root, "kokoro-platform");
    const webRoot = resolve(root, "kokoro-web");

    await runCommand(PLATFORM_MIGRATE_COMMAND, { cwd: platformRoot, env: platformEnv });
    await runCommand(PLATFORM_SEED_COMMAND, { cwd: platformRoot, env: platformEnv });
    const platform = start(PLATFORM_START_COMMAND, { cwd: platformRoot, env: platformEnv });
    await waitHttp(`http://127.0.0.1:${port}/healthz`, { child: platform });
    await runCommand(WEB_PROBE_COMMAND, { cwd: webRoot, env: webEnv });
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
  CONTRACT_DIGEST,
  PLATFORM_MIGRATE_COMMAND,
  PLATFORM_SEED_COMMAND,
  PLATFORM_START_COMMAND,
  WEB_PROBE_COMMAND,
  WORKLOAD_SECRET,
  buildPlatformEnvironment,
  buildResult,
  buildWebEnvironment,
  childExited,
  stopChild,
  validateLease,
};
