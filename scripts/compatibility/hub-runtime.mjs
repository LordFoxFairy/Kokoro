#!/usr/bin/env node

import { generateKeyPairSync, X509Certificate } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { connect as connectHttp2 } from "node:http2";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createServer as createNetServer } from "node:net";
import { fileURLToPath, pathToFileURL } from "node:url";
import { writeSync } from "node:fs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const REQUIRED_RESOURCES = ["mongo"];
const SAFE_PARENT_ENV_KEYS = ["PATH", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP", "PNPM_HOME"];
const MAX_DURATION_MS = 179_999;
const MAX_PROBE_OUTPUT_BYTES = 16 * 1024;
const children = new Set();
const processErrors = new WeakMap();

const ADMIN_SECRET = "compatibility-admin-not-real";
const MASTER_KEY = Buffer.alloc(32, 7).toString("base64");
const PLATFORM_IDENTITY = "spiffe://kokoro.internal/platform";
const AGENT_IDENTITY = "spiffe://kokoro.internal/agent";
const HUB_IDENTITY = "spiffe://kokoro.internal/hub";
const SIGNING_KEY_REF = "hub-signing:compatibility";

export const HUB_HTTP_START_COMMAND = ["pnpm", "--filter", "@kokoro/hub", "run", "dev"];
export const HUB_CONNECT_START_COMMAND = ["pnpm", "--filter", "@kokoro/hub", "run", "dev:connect"];
export const PLATFORM_FIXTURE_COMMAND = [
  "pnpm", "exec", "tsx", resolve(root, "scripts/compatibility/hub-runtime-platform-fixture.mts"),
];
export const AGENT_PROBE_COMMAND = [
  "uv", "run", "--locked", "python", resolve(root, "scripts/compatibility/hub_runtime_agent.py"),
];
export const ASSERTION_IDS = [
  "hub-runtime:platform-provider-ready",
  "hub-runtime:admin-skill-published",
  "hub-runtime:catalog-publication-committed",
  "hub-runtime:agent-resolve-execution-assembly",
  "hub-runtime:agent-fetch-skill-artifact",
  "hub-runtime:artifact-integrity-verified",
  "hub-runtime:non-agent-runtime-rejected",
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
    value.mongo?.database !== databaseStem
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

export function buildHttpEnvironment(
  lease,
  { port, workspaceConfig, parentEnv = process.env },
) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    KOKORO_HUB_PORT: String(port),
    KOKORO_HUB_MONGO_URL: "mongodb://127.0.0.1:27017/?directConnection=true",
    KOKORO_HUB_MONGO_DB: lease.mongo.database,
    KOKORO_WORKSPACE_CONFIG: workspaceConfig,
    KOKORO_HUB_SECRET_MASTER_KEY: MASTER_KEY,
    KOKORO_INTERNAL_SECRET_ADMIN: ADMIN_SECRET,
  });
}

export function buildConnectEnvironment(
  lease,
  { port, projectionPort, workspaceConfig, trust, parentEnv = process.env },
) {
  validateLease(lease);
  return isolatedEnvironment(parentEnv, {
    NODE_ENV: "test",
    KOKORO_HUB_CONNECT_PORT: String(port),
    KOKORO_HUB_MONGO_URL: "mongodb://127.0.0.1:27017/?directConnection=true",
    KOKORO_HUB_MONGO_DB: lease.mongo.database,
    KOKORO_WORKSPACE_CONFIG: workspaceConfig,
    KOKORO_HUB_SECRET_MASTER_KEY: MASTER_KEY,
    KOKORO_HUB_CATALOG_PLATFORM_CALLER_SAN_URI: PLATFORM_IDENTITY,
    KOKORO_HUB_RUNTIME_AGENT_CALLER_SAN_URI: AGENT_IDENTITY,
    KOKORO_HUB_CONNECT_MTLS_PEERS_FILE: trust.peers,
    KOKORO_HUB_CONNECT_TLS_KEY_FILE: trust.serverKey,
    KOKORO_HUB_CONNECT_TLS_CERT_FILE: trust.serverCert,
    KOKORO_HUB_CONNECT_TLS_CLIENT_CA_FILE: trust.ca,
    KOKORO_HUB_CAPABILITY_SIGNING_KEY_FILE: trust.signingKey,
    KOKORO_HUB_CAPABILITY_SIGNING_KEY_REF: SIGNING_KEY_REF,
    KOKORO_HUB_PLATFORM_PROJECTION_BASE_URL: `https://localhost:${projectionPort}`,
    KOKORO_HUB_PLATFORM_PROJECTION_SERVER_NAME: "localhost",
    KOKORO_HUB_PLATFORM_PROJECTION_CLIENT_KEY_FILE: trust.hubKey ?? trust.platformKey,
    KOKORO_HUB_PLATFORM_PROJECTION_CLIENT_CERT_FILE: trust.hubCert ?? trust.platformCert,
    KOKORO_HUB_PLATFORM_PROJECTION_SERVER_CA_FILE: trust.ca,
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
    stdio: capture
      ? ["ignore", "pipe", process.env.KOKORO_COMPAT_DEBUG === "1" ? "inherit" : "ignore"]
      : process.env.KOKORO_COMPAT_DEBUG === "1" ? ["ignore", "inherit", "inherit"] : "ignore",
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
      if (response.status === 200) return;
    } catch {}
    await new Promise((done) => setTimeout(done, 200));
  }
  throw new Error("compatibility_service_not_ready");
}

async function http2Status({ port, path, ca, cert, key }) {
  return new Promise((done, reject) => {
    const client = connectHttp2(`https://localhost:${port}`, {
      ca,
      cert,
      key,
      servername: "localhost",
      rejectUnauthorized: true,
      minVersion: "TLSv1.3",
    });
    let settled = false;
    const fail = (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      client.destroy();
      reject(error);
    };
    const timer = setTimeout(() => {
      fail(new Error("compatibility_http2_timeout"));
    }, 2_000);
    client.once("error", fail);
    const request = client.request({ ":method": "GET", ":path": path });
    request.once("error", fail);
    request.once("response", (headers) => {
      const status = Number(headers[":status"]);
      request.resume();
      request.once("end", () => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        client.close();
        done(status);
      });
    });
    request.end();
  });
}

async function waitHttp2(options, child, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (childExited(child)) throw new Error("compatibility_service_exited");
    try {
      if (await http2Status(options) === 200) return;
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

function runCommand(command, args) {
  const result = spawnSync(command, args, { encoding: "utf8", stdio: ["ignore", "ignore", "ignore"] });
  if (result.status !== 0) throw new Error("compatibility_trust_generation_failed");
}

async function certificate({ directory, caCert, caKey, name, san }) {
  const key = join(directory, `${name}-key.pem`);
  const csr = join(directory, `${name}.csr`);
  const cert = join(directory, `${name}.pem`);
  const extensions = join(directory, `${name}-extensions.cnf`);
  await writeFile(extensions, `subjectAltName=${san}\n`, { mode: 0o600 });
  runCommand("openssl", [
    "req", "-new", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", csr,
    "-subj", `/CN=${name}`, "-addext", `subjectAltName=${san}`,
  ]);
  runCommand("openssl", [
    "x509", "-req", "-in", csr, "-CA", caCert, "-CAkey", caKey, "-CAcreateserial",
    "-out", cert, "-days", "1", "-sha256", "-extfile", extensions,
  ]);
  await chmod(key, 0o600);
  return { key, cert };
}

async function trustMaterial(directory) {
  const caKey = join(directory, "ca-key.pem");
  const ca = join(directory, "ca.pem");
  runCommand("openssl", [
    "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", caKey, "-out", ca,
    "-days", "1", "-sha256", "-subj", "/CN=Kokoro compatibility CA",
  ]);
  await chmod(caKey, 0o600);
  const server = await certificate({ directory, caCert: ca, caKey, name: "server", san: "DNS:localhost" });
  const platform = await certificate({ directory, caCert: ca, caKey, name: "platform", san: `URI:${PLATFORM_IDENTITY}` });
  const agent = await certificate({ directory, caCert: ca, caKey, name: "agent", san: `URI:${AGENT_IDENTITY}` });
  const hub = await certificate({ directory, caCert: ca, caKey, name: "hub", san: `URI:${HUB_IDENTITY}` });
  const signingKey = join(directory, "catalog-signing-key.pem");
  const publicKey = join(directory, "catalog-signing-public.pem");
  const signing = generateKeyPairSync("ed25519");
  await Promise.all([
    writeFile(signingKey, signing.privateKey.export({ format: "pem", type: "pkcs8" }), { mode: 0o600 }),
    writeFile(publicKey, signing.publicKey.export({ format: "pem", type: "spki" }), { mode: 0o600 }),
  ]);
  const peers = join(directory, "hub-peers.json");
  const platformCertificate = new X509Certificate(await readFile(platform.cert));
  const agentCertificate = new X509Certificate(await readFile(agent.cert));
  await writeFile(peers, `${JSON.stringify({ version: 1, peers: [
    { sanUri: PLATFORM_IDENTITY, fingerprint256: platformCertificate.fingerprint256 },
    { sanUri: AGENT_IDENTITY, fingerprint256: agentCertificate.fingerprint256 },
  ] })}\n`, { mode: 0o600 });
  return {
    ca,
    serverCert: server.cert,
    serverKey: server.key,
    platformCert: platform.cert,
    platformKey: platform.key,
    agentCert: agent.cert,
    agentKey: agent.key,
    hubCert: hub.cert,
    hubKey: hub.key,
    peers,
    signingKey,
    publicKey,
  };
}

async function run() {
  const started = Date.now();
  let passed = false;
  let temporary = null;
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (typeof scopePath !== "string" || scopePath.length === 0) throw new Error("compatibility_scope_missing");
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    temporary = await mkdtemp(join(tmpdir(), "kokoro-hub-runtime-"));
    await chmod(temporary, 0o700);
    const packageRoot = join(temporary, "hub-packages");
    const workspaceRoot = join(temporary, "workspace");
    await Promise.all([mkdir(packageRoot), mkdir(workspaceRoot)]);
    const workspaceConfig = join(temporary, "workspace.yaml");
    await writeFile(workspaceConfig, [
      "workspace:",
      "  type: local",
      `  root: ${workspaceRoot}`,
      "hub:",
      "  type: local",
      `  root: ${packageRoot}`,
      "",
    ].join("\n"), { mode: 0o600 });
    const trust = await trustMaterial(temporary);
    const [httpPort, connectPort, projectionPort] = await Promise.all([freePort(), freePort(), freePort()]);
    const platformRoot = resolve(root, "kokoro-platform");
    const agentRoot = resolve(root, "kokoro-agent");
    const safeEnvironment = isolatedEnvironment(process.env, {});
    const probeEnvironment = process.env.KOKORO_COMPAT_DEBUG === "1"
      ? { ...safeEnvironment, KOKORO_COMPAT_DEBUG: "1" }
      : safeEnvironment;

    const projection = start([
      ...PLATFORM_FIXTURE_COMMAND,
      "projection",
      "--port", String(projectionPort),
      "--tls-key", trust.serverKey,
      "--tls-cert", trust.serverCert,
      "--client-ca", trust.ca,
      "--hub-cert", trust.hubCert,
      "--hub-identity", HUB_IDENTITY,
      "--public-key", trust.publicKey,
      "--signing-key-ref", SIGNING_KEY_REF,
    ], { cwd: platformRoot, env: safeEnvironment });
    const ca = await readFile(trust.ca);
    await waitHttp2({
      port: projectionPort,
      path: "/health/ready",
      ca,
      cert: await readFile(trust.hubCert),
      key: await readFile(trust.hubKey),
    }, projection);

    const http = start(HUB_HTTP_START_COMMAND, {
      cwd: platformRoot,
      env: buildHttpEnvironment(lease, { port: httpPort, workspaceConfig }),
    });
    await waitHttp(`http://127.0.0.1:${httpPort}/healthz`, http);
    const hub = start(HUB_CONNECT_START_COMMAND, {
      cwd: platformRoot,
      env: buildConnectEnvironment(lease, { port: connectPort, projectionPort, workspaceConfig, trust }),
    });
    await waitHttp2({
      port: connectPort,
      path: "/health/ready",
      ca,
      cert: await readFile(trust.platformCert),
      key: await readFile(trust.platformKey),
    }, hub);

    const publication = await runProbe([
      ...PLATFORM_FIXTURE_COMMAND,
      "publish",
      "--http-url", `http://127.0.0.1:${httpPort}`,
      "--hub-url", `https://localhost:${connectPort}`,
      "--server-name", "localhost",
      "--admin-secret", ADMIN_SECRET,
      "--ca", trust.ca,
      "--cert", trust.platformCert,
      "--key", trust.platformKey,
    ], { cwd: platformRoot, env: safeEnvironment });
    if (publication?.projectionState !== "committed" ||
        !/^agent-catalog:sha256:[0-9a-f]{64}$/u.test(publication?.agentCatalogRef ?? "")) {
      throw new Error("compatibility_publication_invalid");
    }
    const fixturePath = join(temporary, "publication.json");
    await writeFile(fixturePath, `${JSON.stringify(publication)}\n`, { mode: 0o600 });

    const commonProbe = [
      "--fixture", fixturePath,
      "--rpc-url", `https://localhost:${connectPort}`,
      "--server-name", "localhost",
      "--ca", trust.ca,
      "--key", trust.agentKey,
    ];
    const agent = await runProbe([
      ...AGENT_PROBE_COMMAND,
      ...commonProbe,
      "--cert", trust.agentCert,
      "--cache", join(temporary, "agent-cache"),
    ], { cwd: agentRoot, env: probeEnvironment });
    if (agent?.schemaVersion !== 1 || agent.resolvedSkills !== 1 || agent.fetchedArtifacts !== 1 ||
        agent.bodySha256 !== publication.expectedBodySha256 ||
        !/^[0-9a-f]{64}$/u.test(agent.assemblyDigest ?? "")) {
      throw new Error("compatibility_agent_probe_invalid");
    }
    const rejected = await runProbe([
      ...AGENT_PROBE_COMMAND,
      "--fixture", fixturePath,
      "--rpc-url", `https://localhost:${connectPort}`,
      "--server-name", "localhost",
      "--ca", trust.ca,
      "--cert", trust.platformCert,
      "--key", trust.platformKey,
      "--cache", join(temporary, "non-agent-cache"),
      "--expect-rejected",
    ], { cwd: agentRoot, env: probeEnvironment });
    if (rejected?.schemaVersion !== 1 || rejected.rejected !== true) {
      throw new Error("compatibility_non_agent_probe_invalid");
    }
    passed = true;
  } catch (error) {
    if (process.env.KOKORO_COMPAT_DEBUG === "1") {
      process.stderr.write(`${error instanceof Error ? error.message : "hub_runtime_live_failed"}\n`);
    }
    passed = false;
  }
  const cleanup = await stopAll();
  if (temporary !== null) {
    try {
      if (process.env.KOKORO_COMPAT_DEBUG === "1" && process.env.KOKORO_COMPAT_KEEP_TEMP === "1") {
        process.stderr.write(`hub_runtime_temp:${temporary}\n`);
      } else {
        await rm(temporary, { recursive: true, force: true });
      }
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
