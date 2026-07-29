import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";

const scenarioUrl = new URL("./admin-auth-connect.mjs", import.meta.url);

test("Admin Auth compatibility adapter is code-owned by Root", async () => {
  await assert.doesNotReject(access(scenarioUrl));
});

const adapter = await import(scenarioUrl);
const lease = {
  schemaVersion: 1,
  runId: "run_fixture",
  endpointFingerprint: "kokoro-infra.local",
  resources: ["mongo", "mysql", "redis"],
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
};

test("validates only a Root-leased Admin database identity", () => {
  assert.equal(typeof adapter.validateLease, "function");
  assert.equal(adapter.validateLease(lease), lease);
  for (const invalid of [
    { ...lease, resources: ["mongo", "redis"] },
    { ...lease, mysql: { ...lease.mysql, admin: "kokoro_admin" } },
    { ...lease, mysqlUsers: { ...lease.mysqlUsers, admin: { username: "root", password: "pw" } } },
  ]) {
    assert.throws(() => adapter.validateLease(invalid), /compatibility_scope_invalid/u);
  }
});

test("treats both normal exit and signal termination as child completion", () => {
  assert.equal(typeof adapter.childExited, "function");
  assert.equal(adapter.childExited({ exitCode: 0, signalCode: null }), true);
  assert.equal(adapter.childExited({ exitCode: null, signalCode: "SIGTERM" }), true);
  assert.equal(adapter.childExited({ exitCode: null, signalCode: null }), false);
});

function processExists(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error.code === "ESRCH") return false;
    throw error;
  }
}

async function waitForProcessesToExit(pids) {
  const deadline = Date.now() + 3_000;
  while (Date.now() < deadline) {
    if (pids.every((pid) => !processExists(pid))) return;
    await new Promise((done) => setTimeout(done, 25));
  }
  assert.fail(`process group still alive: ${pids.filter(processExists).join(",")}`);
}

test("cleanup terminates the complete detached provider process group", async () => {
  assert.equal(typeof adapter.stopChild, "function");
  const directory = await mkdtemp(resolve(tmpdir(), "kokoro-admin-auth-process-group-"));
  const marker = resolve(directory, "pids.json");
  const script = [
    'const { spawn } = require("node:child_process")',
    'const { writeFileSync } = require("node:fs")',
    'const child = spawn(process.execPath, ["-e", "setInterval(() => {}, 1000)"], { stdio: "ignore" })',
    'writeFileSync(process.argv[1], JSON.stringify({ parent: process.pid, child: child.pid }))',
    'setInterval(() => {}, 1000)',
  ].join(";");
  const parent = spawn(process.execPath, ["-e", script, marker], {
    cwd: directory,
    detached: true,
    shell: false,
    stdio: "ignore",
  });
  try {
    const deadline = Date.now() + 3_000;
    while (Date.now() < deadline) {
      try {
        await access(marker);
        break;
      } catch {
        await new Promise((done) => setTimeout(done, 25));
      }
    }
    const pids = JSON.parse(await readFile(marker, "utf8"));
    await adapter.stopChild(parent);
    await waitForProcessesToExit([pids.parent, pids.child]);
  } finally {
    if (!adapter.childExited(parent) && parent.pid !== undefined) process.kill(-parent.pid, "SIGKILL");
    await rm(directory, { recursive: true, force: true });
  }
});

test("builds isolated Platform and Web environments with the same attested contract", () => {
  assert.equal(typeof adapter.buildPlatformEnvironment, "function");
  assert.equal(typeof adapter.buildWebEnvironment, "function");
  const parentEnv = {
    PATH: "/example/bin",
    LANG: "en_US.UTF-8",
    HOME: "/sensitive/home",
    DATABASE_URL_ADMIN: "mysql://parent-secret",
    KOKORO_ADMIN_PROXY_SECRET: "parent-secret",
    OPENAI_API_KEY: "parent-secret",
  };
  const platform = adapter.buildPlatformEnvironment(lease, { port: 4291, parentEnv });
  const web = adapter.buildWebEnvironment({ platformPort: 4291, parentEnv });

  assert.equal(platform.PATH, parentEnv.PATH);
  assert.equal(platform.LANG, parentEnv.LANG);
  assert.equal(platform.HOME, undefined);
  assert.equal(platform.OPENAI_API_KEY, undefined);
  assert.equal(platform.KOKORO_ADMIN_PORT, "4291");
  assert.equal(platform.KOKORO_ADMIN_PROXY_SECRETS, adapter.WORKLOAD_SECRET);
  assert.equal(platform.KOKORO_ADMIN_AUTH_CONTRACT_DIGEST, adapter.CONTRACT_DIGEST);
  const databaseUrl = new URL(platform.DATABASE_URL_ADMIN);
  assert.equal(databaseUrl.hostname, "127.0.0.1");
  assert.equal(databaseUrl.port, "3307");
  assert.equal(databaseUrl.pathname, `/${lease.mysql.admin}`);
  assert.equal(databaseUrl.username, lease.mysqlUsers.admin.username);
  assert.equal(databaseUrl.password, lease.mysqlUsers.admin.password);

  assert.equal(web.PATH, parentEnv.PATH);
  assert.equal(web.HOME, undefined);
  assert.equal(web.OPENAI_API_KEY, undefined);
  assert.equal(web.KOKORO_GATEWAY_URL, "http://127.0.0.1:4291");
  assert.equal(web.KOKORO_ADMIN_PROXY_SECRET, adapter.WORKLOAD_SECRET);
  assert.equal(web.KOKORO_ADMIN_AUTH_CONTRACT_DIGEST, adapter.CONTRACT_DIGEST);
  assert.notEqual(web.KOKORO_ADMIN_PROXY_SECRET, parentEnv.KOKORO_ADMIN_PROXY_SECRET);
});

test("uses only official child commands and no shell fragments", () => {
  assert.deepEqual(adapter.PLATFORM_MIGRATE_COMMAND, [
    "pnpm", "--filter", "@kokoro/platform-admin", "run", "db:migrate",
  ]);
  assert.deepEqual(adapter.PLATFORM_SEED_COMMAND, [
    "pnpm", "--filter", "@kokoro/platform-admin", "run", "db:seed",
  ]);
  assert.deepEqual(adapter.PLATFORM_START_COMMAND, [
    "pnpm", "--filter", "@kokoro/platform-admin", "run", "start",
  ]);
  assert.deepEqual(adapter.WEB_PROBE_COMMAND, [
    "pnpm", "--filter", "@kokoro/admin-web", "run", "compat:admin-auth",
  ]);
});

test("the Web consumer owns the generated-client live probe command", async () => {
  const packageJson = JSON.parse(
    await readFile(new URL("../../kokoro-web/apps/admin/package.json", import.meta.url), "utf8"),
  );
  assert.equal(
    packageJson.scripts["compat:admin-auth"],
    "vitest run lib/auth/client.test.ts lib/auth/live-compatibility.test.ts",
  );
});

test("emits one closed result with every required business assertion", () => {
  assert.equal(typeof adapter.buildResult, "function");
  assert.deepEqual(adapter.buildResult(true, Number.MAX_SAFE_INTEGER), {
    schemaVersion: 1,
    scenarioId: "platform-admin-auth-connect",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: [
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
      "admin-v2:mtls-peer-bound",
      "admin-v2:command-digest-verified",
      "admin-v2:operator-generation-bound",
      "admin-v2:phishing-resistant-step-up-bound",
      "admin-v2:maker-checker-independent",
      "admin-v2:checker-queues-only",
      "admin-v2:worker-owner-operation",
      "admin-v2:frozen-authority-epoch",
      "admin-v2:effect-terminal-atomic",
      "admin-v2:stale-authority-no-effect",
      "admin-v2:receipt-idempotent-recovery",
      "admin-v2:break-glass-post-review",
      "admin-v2:legacy-authority-unreachable",
    ],
    durationMs: 179_999,
  });
  assert.equal(adapter.buildResult(false, -1).durationMs, 0);
  assert.equal(adapter.buildResult(false, 12).reasonCode, "platform_admin_auth_live_failed");
});

test("adapter cannot use child Compose, raw SQL, env files, sibling imports, or observable logs", async () => {
  const source = await readFile(scenarioUrl, "utf8");
  assert.doesNotMatch(source, /docker(?:\s+compose)?|compose\.ya?ml/iu);
  assert.doesNotMatch(source, /(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE\s+TABLE)\s/iu);
  assert.doesNotMatch(source, /(?:readFile|dotenv|--env-file)[^\n]*\.env/iu);
  assert.doesNotMatch(source, /import[^\n]*(?:kokoro-platform|kokoro-web)/u);
  assert.doesNotMatch(source, /console\.(?:log|error|warn)|process\.(?:stdout|stderr)\.write/u);
  assert.match(source, /detached:\s*true/u);
  assert.match(source, /process\.kill\(-child\.pid/u);
  assert.match(source, /finally\s*\{[\s\S]*stopAll/u);
  assert.match(source, /writeSync\(3,/u);
});
