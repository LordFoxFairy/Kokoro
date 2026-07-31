import assert from "node:assert/strict";
import { lstat, mkdtemp, mkdir, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";

import * as runner from "./run-pinned-compatibility.mjs";

const {
  parseRunnerArguments,
  runCompatibility,
  runScenarioProcess,
  sanitizeText,
  validateEvidenceTarget,
  validateScenarioResult,
} = runner;

const ids = ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"];
const pins = Object.fromEntries(ids.map((id, index) => [id, String(index + 1).repeat(40)]));

function matrix() {
  return {
    schemaVersion: 1,
    combinationId: "fixture-combination",
    contracts: [
      { id: "session-browser", version: 1, providers: ["kokoro-session"], consumers: ["kokoro-web"] },
      { id: "platform-runtime", version: 1, providers: ["kokoro-platform"], consumers: ["kokoro-session"] },
      { id: "session-agent-execution", version: 1, providers: ["kokoro-agent"], consumers: ["kokoro-session"] },
      { id: "model-gateway", version: 1, providers: ["kokoro-platform"], consumers: ["kokoro-agent"] },
    ],
    requiredGates: ["root-infra-runtime-smoke"],
    runtimeGate: {
      schemaVersion: 1,
      requiredServices: ["postgres", "redis", "mongo", "minio", "litellm"],
      scenarios: [
        { id: "web-session-http-sse", commandId: "node-web-session-http-sse-v1", required: true, participants: ["kokoro-session", "kokoro-web"], protocols: [{ id: "session-browser", version: 1 }], timeoutSeconds: 180 },
        { id: "session-platform-internal-rpc", commandId: "node-session-platform-internal-rpc-v1", required: true, participants: ["kokoro-platform", "kokoro-session"], protocols: [{ id: "platform-runtime", version: 1 }], timeoutSeconds: 180 },
        { id: "session-agent-durable-localfake", commandId: "python-session-agent-durable-v1", required: true, participants: ["kokoro-agent", "kokoro-session"], protocols: [{ id: "session-agent-execution", version: 1 }], timeoutSeconds: 300 },
        { id: "agent-model-gateway-localfake", commandId: "python-agent-model-gateway-v1", required: true, participants: ["kokoro-agent", "kokoro-platform"], protocols: [{ id: "model-gateway", version: 1 }], timeoutSeconds: 180 },
      ],
    },
  };
}

function manifest() {
  return {
    schemaVersion: 1,
    repositoryTopology: "federated-submodules-v1",
    repositories: ids.map((id) => ({ id, pin: pins[id] })),
  };
}

async function fixture() {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-compatibility-"));
  await mkdir(resolve(root, "tmp"));
  await writeFile(resolve(root, ".gitignore"), "tmp/\n");
  const matrixPath = resolve(root, "matrix.json");
  const manifestPath = resolve(root, "manifest.json");
  const evidencePath = resolve(root, "tmp/evidence.json");
  const infraEnvFile = resolve(root, "infra.env");
  await writeFile(matrixPath, `${JSON.stringify(matrix())}\n`);
  await writeFile(manifestPath, `${JSON.stringify(manifest())}\n`);
  await writeFile(infraEnvFile, "KOKORO_INFRA_FIXTURE=not-read\n");
  return { root, matrixPath, manifestPath, evidencePath, infraEnvFile };
}

function dependencies(overrides = {}) {
  const calls = { cleanup: 0, scenarios: [], verify: 0, writes: [] };
  const deps = {
    now: (() => {
      let tick = 0;
      return () => new Date(1_700_000_000_000 + tick++ * 100).toISOString();
    })(),
    verifyPins: async () => {
      calls.verify += 1;
      return { ...pins };
    },
    preflightServices: async (services) => services.map((id) => ({ id, healthy: true })),
    acquireLease: async () => ({
      runId: "run_fixture",
      leaseToken: "not-recorded",
      stateRoot: "/fixture/state",
      endpointFingerprint: "fixture-endpoint",
    }),
    provisionScope: async () => {},
    cleanupScope: async () => { calls.cleanup += 1; },
    runScenario: async (scenario) => {
      calls.scenarios.push(scenario.id);
      return {
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: "pass",
        reasonCode: "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      };
    },
    onEvidence: (value) => calls.writes.push(value.outcome),
    ...overrides,
  };
  return { deps, calls };
}

test("CLI accepts only matrix, manifest, tree, ignored tmp evidence, and an Infra env file", () => {
  assert.deepEqual(parseRunnerArguments([
    "--matrix", "matrix.json",
    "--manifest", "manifest.json",
    "--tree", "index",
    "--evidence", "tmp/evidence.json",
    "--infra-env-file", "tmp/ci-infra.env",
  ], "/repo"), {
    root: "/repo",
    matrixPath: "/repo/matrix.json",
    manifestPath: "/repo/manifest.json",
    tree: "index",
    evidencePath: "/repo/tmp/evidence.json",
    infraEnvFile: "/repo/tmp/ci-infra.env",
  });
  assert.throws(() => parseRunnerArguments(["--tree", "branch"], "/repo"), /compatibility_arguments/u);
  assert.throws(() => parseRunnerArguments(["--command", "sh -c anything"], "/repo"), /compatibility_arguments/u);
});

test("CLI rejects every repeated single-value argument before any external boundary", async () => {
  const item = await fixture();
  let externalBoundaryCalls = 0;
  const duplicates = [
    ["--matrix", "first-matrix.json", "second-matrix.json"],
    ["--manifest", "first-manifest.json", "second-manifest.json"],
    ["--tree", "head", "index"],
    ["--evidence", "tmp/first-evidence.json", "tmp/second-evidence.json"],
    ["--infra-env-file", "first-infra.env", "second-infra.env"],
  ];
  try {
    for (const [argument, first, second] of duplicates) {
      await assert.rejects(async () => {
        const options = parseRunnerArguments([
          "--evidence", "tmp/evidence.json",
          argument, first,
          argument, second,
        ], item.root);
        externalBoundaryCalls += 1;
        await runCompatibility(options, dependencies().deps);
      }, /compatibility_arguments/u, argument);
    }
    assert.equal(externalBoundaryCalls, 0);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("PostgreSQL-only runner ignores Infra env-file and omits MySQL scope authority", async () => {
  const item = await fixture();
  const legacySecret = "legacy-parent-secret";
  const scopeCalls = { cleanup: [], provision: [] };
  const preflightCalls = [];
  const scenarioEnvironments = [];
  const options = {
    ...item,
    infraEnvFile: resolve(item.root, "missing-and-not-read.env"),
  };
  const { deps } = dependencies({
    environment: {
      PATH: process.env.PATH,
      MYSQL_ROOT_PASSWORD: legacySecret,
    },
    openInfraEnvFile: async () => {
      assert.fail("PostgreSQL-only compatibility must not read an Infra credential file");
    },
    preflightServices: async (services) => {
      preflightCalls.push([...services]);
      return services.map((id) => ({ id, healthy: true }));
    },
    provisionScope: async (scopeOptions) => { scopeCalls.provision.push(scopeOptions); },
    cleanupScope: async (scopeOptions) => { scopeCalls.cleanup.push(scopeOptions); },
    runScenario: async (scenario, context) => {
      scenarioEnvironments.push(context.environment);
      return {
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: "pass",
        reasonCode: "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      };
    },
  });
  try {
    const result = await runCompatibility(options, deps);
    assert.equal(result.exitCode, 0);
    assert.deepEqual(preflightCalls, [[
      "postgres",
      "redis",
      "mongo",
      "minio",
      "litellm",
    ]]);
    assert.equal(scopeCalls.provision.length, 1);
    assert.equal(scopeCalls.cleanup.length, 1);
    assert.ok([...scopeCalls.provision, ...scopeCalls.cleanup].every(
      (scopeOptions) => !Object.hasOwn(scopeOptions, "mysqlRootPassword"),
    ));
    assert.ok(scenarioEnvironments.every((environment) =>
      Object.keys(environment).every((key) => key.toLowerCase() !== "mysql_root_password")));
    const serializedEvidence = await readFile(item.evidencePath, "utf8");
    assert.equal(serializedEvidence.includes(legacySecret), false);
    assert.equal(serializedEvidence.includes(options.infraEnvFile), false);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("code-owned scenario commands point at existing root adapters", async () => {
  const source = await readFile(new URL("./run-pinned-compatibility.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /scripts\/compatibility\/session-agent-durable\.py/u);
  assert.match(source, /scripts\/compatibility\/session_agent_durable\.py/u);
  assert.doesNotMatch(source, /scripts\/compatibility\/admin-auth-connect\.mjs/u);
  assert.match(source, /scripts\/compatibility\/hub-runtime\.mjs/u);
});

test("evidence target must be inside ignored tmp and cannot traverse a symlink", async () => {
  const item = await fixture();
  try {
    await assert.doesNotReject(validateEvidenceTarget(item.root, item.evidencePath));
    await assert.rejects(validateEvidenceTarget(item.root, resolve(item.root, "evidence.json")), /compatibility_evidence_path/u);
    const outside = await mkdtemp(resolve(tmpdir(), "kokoro-compatibility-outside-"));
    await symlink(outside, resolve(item.root, "tmp/link"));
    await assert.rejects(validateEvidenceTarget(item.root, resolve(item.root, "tmp/link/evidence.json")), /compatibility_evidence_symlink/u);
    await rm(outside, { recursive: true, force: true });
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("sanitizer removes common credential forms", () => {
  const source = "Authorization: Bearer abc.def.ghi PASSWORD=hunter2 https://user:pass@example.test -----BEGIN PRIVATE KEY-----";
  const sanitized = sanitizeText(source);
  for (const secret of ["abc.def.ghi", "hunter2", "user:pass", "PRIVATE KEY"]) {
    assert.equal(sanitized.includes(secret), false);
  }
});

test("machine scenario result is closed and cannot report free-form details", () => {
  const result = {
    schemaVersion: 1,
    scenarioId: "web-session-http-sse",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: ["web-session:proxy", "web-session:sse-resume"],
    durationMs: 12,
  };
  assert.deepEqual(validateScenarioResult(result, "web-session-http-sse"), result);
  assert.throws(() => validateScenarioResult({ ...result, detail: "Bearer secret" }, result.scenarioId), /compatibility_scenario_result/u);
  assert.throws(() => validateScenarioResult({ ...result, outcome: "skip" }, result.scenarioId), /compatibility_scenario_result/u);
});

test("successful run writes running then pass evidence with exact four pins", async () => {
  const item = await fixture();
  const { deps, calls } = dependencies();
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 0);
    assert.equal(result.evidence.outcome, "pass");
    assert.deepEqual(result.evidence.repositories, ids.map((id) => ({ id, sha: pins[id] })));
    assert.deepEqual(calls.writes, ["running", "pass"]);
    assert.equal(calls.verify, 2);
    assert.equal(calls.cleanup, 1);
    assert.deepEqual(calls.scenarios, matrix().runtimeGate.scenarios.map(({ id }) => id));
    assert.equal((await lstat(item.evidencePath)).mode & 0o777, 0o600);
    assert.equal(JSON.parse(await readFile(item.evidencePath, "utf8")).outcome, "pass");
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("scope-file removal failure still performs lease cleanup", async () => {
  const item = await fixture();
  const cleanupCalls = [];
  let replaced = false;
  const { deps } = dependencies({
    cleanupScope: async (options) => { cleanupCalls.push(options); },
    runScenario: async (scenario, context) => {
      if (!replaced) {
        await rm(context.scopeFile);
        await mkdir(context.scopeFile);
        replaced = true;
      }
      return {
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: "pass",
        reasonCode: "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      };
    },
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 3);
    assert.equal(result.evidence.reasonCode, "scope_file_cleanup_failed");
    assert.equal(cleanupCalls.length, 1);
    assert.equal(Object.hasOwn(cleanupCalls[0], "mysqlRootPassword"), false);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("lease cleanup failure takes priority over scope-file removal failure", async () => {
  const item = await fixture();
  const cleanupCalls = [];
  let replaced = false;
  const { deps } = dependencies({
    cleanupScope: async (options) => {
      cleanupCalls.push(options);
      throw new Error("fixture cleanup failure");
    },
    runScenario: async (scenario, context) => {
      if (!replaced) {
        await rm(context.scopeFile);
        await mkdir(context.scopeFile);
        replaced = true;
      }
      return {
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: "pass",
        reasonCode: "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      };
    },
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 3);
    assert.equal(result.evidence.reasonCode, "lease_cleanup_failed");
    assert.equal(cleanupCalls.length, 1);
    assert.equal(Object.hasOwn(cleanupCalls[0], "mysqlRootPassword"), false);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("lease cleanup failure remains final when postflight pins also drift", async () => {
  const item = await fixture();
  let verification = 0;
  const drifted = { ...pins, "kokoro-web": "f".repeat(40) };
  const { deps } = dependencies({
    cleanupScope: async () => { throw new Error("fixture cleanup failure"); },
    verifyPins: async () => (++verification === 1 ? { ...pins } : drifted),
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 3);
    assert.equal(result.evidence.reasonCode, "lease_cleanup_failed");
    assert.equal(result.evidence.postflightPinVerification, "fail");
    assert.equal(
      JSON.parse(await readFile(item.evidencePath, "utf8")).reasonCode,
      "lease_cleanup_failed",
    );
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("scope-file cleanup failure remains final when postflight verification also errors", async () => {
  const item = await fixture();
  let replaced = false;
  let verification = 0;
  const { deps } = dependencies({
    verifyPins: async () => {
      verification += 1;
      if (verification === 1) return { ...pins };
      throw new Error("fixture postflight failure");
    },
    runScenario: async (scenario, context) => {
      if (!replaced) {
        await rm(context.scopeFile);
        await mkdir(context.scopeFile);
        replaced = true;
      }
      return {
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: "pass",
        reasonCode: "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      };
    },
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 3);
    assert.equal(result.evidence.reasonCode, "scope_file_cleanup_failed");
    assert.equal(result.evidence.postflightPinVerification, "fail");
    assert.equal(
      JSON.parse(await readFile(item.evidencePath, "utf8")).reasonCode,
      "scope_file_cleanup_failed",
    );
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("combination digest changes when an attested contract artifact changes", async () => {
  const first = await fixture();
  const second = await fixture();
  try {
    const baseline = await runCompatibility(first, dependencies().deps);
    const attestedMatrix = JSON.parse(await readFile(second.matrixPath, "utf8"));
    attestedMatrix.contracts[0].artifactDigest = "a".repeat(64);
    await writeFile(second.matrixPath, `${JSON.stringify(attestedMatrix)}\n`);
    const attested = await runCompatibility(second, dependencies().deps);
    assert.notEqual(attested.evidence.combinationDigest, baseline.evidence.combinationDigest);
  } finally {
    await rm(first.root, { recursive: true, force: true });
    await rm(second.root, { recursive: true, force: true });
  }
});

test("unhealthy service and required incomplete scenario never produce pass", async () => {
  const first = await fixture();
  try {
    const unhealthy = dependencies({
      preflightServices: async (services) => services.map((id) => ({ id, healthy: id !== "mongo" })),
    });
    const result = await runCompatibility(first, unhealthy.deps);
    assert.equal(result.exitCode, 2);
    assert.equal(result.evidence.outcome, "incomplete");
    assert.deepEqual(unhealthy.calls.scenarios, []);
  } finally {
    await rm(first.root, { recursive: true, force: true });
  }

  const second = await fixture();
  try {
    const incomplete = dependencies({
      runScenario: async (scenario) => ({
        schemaVersion: 1,
        scenarioId: scenario.id,
        outcome: scenario.id === "session-agent-durable-localfake" ? "incomplete" : "pass",
        reasonCode: scenario.id === "session-agent-durable-localfake" ? "required_dependency_missing" : "ok",
        assertionIds: [`${scenario.id}:contract`],
        durationMs: 1,
      }),
    });
    const result = await runCompatibility(second, incomplete.deps);
    assert.equal(result.exitCode, 2);
    assert.equal(result.evidence.outcome, "incomplete");
  } finally {
    await rm(second.root, { recursive: true, force: true });
  }
});

test("pin drift or scenario failure is nonzero and lease cleanup still runs", async () => {
  const item = await fixture();
  let verification = 0;
  const drifted = { ...pins, "kokoro-web": "f".repeat(40) };
  const { deps, calls } = dependencies({
    verifyPins: async () => (++verification === 1 ? { ...pins } : drifted),
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 3);
    assert.equal(result.evidence.outcome, "error");
    assert.equal(result.evidence.reasonCode, "postflight_pin_drift");
    assert.equal(calls.cleanup, 1);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("an interrupted required scenario produces interrupted evidence and still cleans the lease", async () => {
  const item = await fixture();
  const { deps, calls } = dependencies({
    runScenario: async (scenario) => ({
      schemaVersion: 1,
      scenarioId: scenario.id,
      outcome: "interrupted",
      reasonCode: "scenario_interrupted",
      assertionIds: [`${scenario.id}:interrupted`],
      durationMs: 1,
    }),
  });
  try {
    const result = await runCompatibility(item, deps);
    assert.equal(result.exitCode, 130);
    assert.equal(result.evidence.outcome, "interrupted");
    assert.equal(result.evidence.reasonCode, "scenario_interrupted");
    assert.equal(calls.cleanup, 1);
    assert.equal(calls.verify, 2);
    assert.deepEqual(calls.scenarios, []);
  } finally {
    await rm(item.root, { recursive: true, force: true });
  }
});

test("scenario process boundary strips exact and case-variant MySQL root credentials", async () => {
  const script = [
    'const keys = Object.keys(process.env).filter((key) => key.toLowerCase() === "mysql_root_password")',
    'require("node:fs").writeFileSync(3, JSON.stringify(keys))',
  ].join(";");
  const result = await runScenarioProcess([process.execPath, "-e", script], {
    cwd: process.cwd(),
    env: {
      PATH: process.env.PATH,
      MYSQL_ROOT_PASSWORD: "legacy-parent-secret",
      Mysql_Root_Password: "case-variant-parent-credential",
    },
    timeoutMs: 3_000,
  });
  assert.equal(result.kind, "exit");
  assert.deepEqual(JSON.parse(result.machineOutput), []);
});

test("scenario timeout terminates the complete detached process group", async () => {
  assert.equal(typeof runScenarioProcess, "function");
  const directory = await mkdtemp(resolve(tmpdir(), "kokoro-process-group-"));
  const marker = resolve(directory, "pids.json");
  const script = [
    'const { spawn } = require("node:child_process")',
    'const { writeFileSync } = require("node:fs")',
    'const child = spawn(process.execPath, ["-e", "setInterval(() => {}, 1000)"], { stdio: "ignore" })',
    'writeFileSync(process.argv[1], JSON.stringify({ parent: process.pid, child: child.pid }))',
    'setInterval(() => {}, 1000)',
  ].join(";");
  try {
    const result = await runScenarioProcess([process.execPath, "-e", script, marker], {
      cwd: directory,
      env: process.env,
      timeoutMs: 500,
    });
    assert.equal(result.kind, "timeout");
    const pids = JSON.parse(await readFile(marker, "utf8"));
    await assertProcessesExit([pids.parent, pids.child]);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

async function assertProcessesExit(pids) {
  const deadline = Date.now() + 3_000;
  while (Date.now() < deadline) {
    if (pids.every((pid) => !processExists(pid))) return;
    await new Promise((done) => setTimeout(done, 25));
  }
  assert.fail(`process group still alive: ${pids.filter(processExists).join(",")}`);
}

function processExists(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error.code === "ESRCH") return false;
    throw error;
  }
}
